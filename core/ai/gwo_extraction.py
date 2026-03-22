import numpy as np
import cv2
from sklearn.cluster import KMeans
from niapy.algorithms.basic import GreyWolfOptimizer
from niapy.problems import Problem
from niapy.task import Task

class KMeansSeededGWO(GreyWolfOptimizer):
    """Subclass of GWO: overrides init_population to use k-means results as the initial population."""
    def __init__(self, seed_population, **kwargs):
        super().__init__(**kwargs)
        self._seed_pop = seed_population  # shape: (pop_size, dim)

    def init_population(self, task):
        # Call the parent class to obtain the population in the standard format
        pop, fpop, d = super().init_population(task)
        # Replace the random initialization with k-means seeds
        for i, individual in enumerate(pop):
            individual.x = self._seed_pop[i].copy()
            individual.f = task.eval(individual.x)
        return pop, fpop, d

from core.colors.color_oklch import _linear_rgb_to_oklab, _srgb_channel_to_linear
from core.colors.color_oklab import oklab_to_hex

def rgb_to_oklab_pixel(r, g, b):
    lr = _srgb_channel_to_linear(r)
    lg = _srgb_channel_to_linear(g)
    lb = _srgb_channel_to_linear(b)
    return _linear_rgb_to_oklab(lr, lg, lb)

class OklabColorQuant(Problem):
    def __init__(self, pixels, k=10):
        self.pixels = pixels
        self.k = k
        lower = np.tile([0.0, -0.5, -0.5], k)
        upper = np.tile([1.0, 0.5, 0.5], k)
        super().__init__(dimension=k*3, lower=lower, upper=upper)

    def _evaluate(self, x):
        centers = x.reshape(self.k, 3)

        # Term 1: Mean Squared Error ( Reconstruction Error )
        # Computes the average squared distance between each pixel and its nearest cluster center.
        # This is equivalent to the k-means objective, ensuring that the palette faithfully
        # represents the true color distribution of the image.
        dists = np.sum((self.pixels[:, None] - centers)**2, axis=-1)
        mse = np.mean(np.min(dists, axis=1))

        # Term 2: Diversity Penalty ( Key advantage of GWO over k-means )
        # Background:
        # Pure MSE minimization ( as in k-means ) tends to place multiple centers
        # in the same dominant color region ( e.g., large blue skies ), leading to
        # redundant and visually similar palette entries.
        #
        # Solution:
        # Compute all pairwise distances between cluster centers in OKLab space,
        # and use the inverse of the minimum distance as a penalty term.
        # Smaller distances produce larger penalties, encouraging the optimizer
        # to spread centers across perceptually distinct regions.
        #
        # Why OKLab?
        # OKLab is a perceptually uniform color space, where Euclidean distance
        # closely matches human color perception. Therefore, enforcing distance
        # here directly improves perceptual diversity.
        #
        # λ = 0.05 is an empirical balance:
        # - Small enough to preserve reconstruction fidelity ( MSE dominance )
        # - Large enough to effectively separate similar centers
        # Increase λ if colors are too similar; decrease if overly dispersed.
        center_dists = np.sum((centers[:, None] - centers[None, :])**2, axis=-1)
        np.fill_diagonal(center_dists, np.inf) # Exclude self-distance
        min_pairwise_dist = np.min(center_dists)
        diversity_penalty = 1.0 / (min_pairwise_dist + 1e-8) # Avoid division by zero

        lam = 0.05 # Weight of the diversity penalty ( λ )
        return mse + lam * diversity_penalty

def extract_top10_oklab(image_path, k=10, sample_ratio=0.3, pop_size=60, max_evals=20000):
    img = cv2.imread(image_path)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB) / 255.0

    # Flatten and sample pixels: increase sampling ratio to 30%,
    # with an upper limit of 30,000 pixels to avoid excessive computation
    pixels_rgb = img.reshape(-1, 3)
    n = len(pixels_rgb)
    sample_n = min(int(n * sample_ratio), 30000)
    idx = np.random.choice(n, sample_n, replace=False)
    sampled_rgb = pixels_rgb[idx]

    # Convert sampled pixels to OKLab color space
    pixels_oklab = np.array([rgb_to_oklab_pixel(*p) for p in sampled_rgb], dtype=np.float64)

    # Use k-means++ to obtain a strong initialization, then refine with GWO
    kmeans = KMeans(n_clusters=k, init="k-means++", n_init=3, random_state=42)
    kmeans.fit(pixels_oklab)
    km_centers = kmeans.cluster_centers_.flatten()  # shape: (k*3,)

    problem = OklabColorQuant(pixels_oklab, k=k)
    task = Task(problem, max_evals=max_evals)

    # Build initial population:
    # First individual = k-means solution
    # Remaining individuals = small Gaussian perturbations around it
    rng = np.random.default_rng(42)
    init_pop = np.clip(
        km_centers + rng.normal(0, 0.02, size=(pop_size, k * 3)),
        problem.lower,
        problem.upper,
    )
    init_pop[0] = np.clip(km_centers, problem.lower, problem.upper)

    algo = KMeansSeededGWO(seed_population=init_pop, population_size=pop_size)
    best_solution, best_mse = algo.run(task)

    # If GWO fails and returns None, fall back to k-means result to ensure robustness
    if best_solution is None:
        centers_oklab = km_centers.reshape(k, 3)
    else:
        centers_oklab = best_solution.reshape(k, 3)

    # Sort by lightness ( L channel ) in descending order
    sort_idx = np.argsort(-centers_oklab[:, 0])
    sorted_centers = centers_oklab[sort_idx]

    # Convert OKLab centers back to RGB
    results_rgb = []
    for center in sorted_centers:
        hex_str = oklab_to_hex(*center)
        h = hex_str.lstrip('#')
        results_rgb.append([int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)])

    return np.array(results_rgb)

# test
if __name__ == "__main__":
    colors = extract_top10_oklab("data/uploads/254bd6e6c931c97c_test.png")
    print("Top 10 dominant colors ( RGB ) :")
    for i, c in enumerate(colors, 1):
        print(f"{i}: {c}  #{c[0]:02x}{c[1]:02x}{c[2]:02x}")
