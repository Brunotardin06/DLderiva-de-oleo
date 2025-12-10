from input_image_generation import *
import xarray as xr
import numpy as np


def main():
    
    X = datageneration(n_dots_per_circle = 100, n_circles = 5, radius_max = 2.5)

    X_clustered = cluster(X, eps = 1.1)

    n_noise = list(X_clustered).count(-1)
    n_clusters = len(set(X_clustered)) - (1 if -1 in X_clustered else 0)
    print(f"Estimated number of clusters: {n_clusters}")
    print(f"Estimated number of noise points: {n_noise}")

    cluster_dict = separation(X, X_clustered)

    vertices_dict = polygondata(cluster_dict)

    image = blackwhitematrix(vertices_dict, step = 0.5, padding_rate=0.1)

    visual(X, X_clustered, image)


if __name__ == '__main__':
    main()