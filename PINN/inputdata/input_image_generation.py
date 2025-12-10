import numpy as np
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
from scipy.spatial import ConvexHull
from skimage.draw import polygon #scikit-image


def datageneration(n_circles = 3, n_dots_per_circle = 200, radius_max = 2):
    '''
    Generates random points to simulate the oil stain particles
    -- Needs to be better --

    returns: ndarray of coordinates of the particles
    '''
    X = np.zeros((n_circles*n_dots_per_circle, 2))

    C = np.zeros((n_circles, 2))
    C[0] = [0,0]
    try:
        C[1] = [5.2,0]
    except IndexError:
        print("Ultrapassou o número de círculos")
    try:
        C[2] = [2.5,4.5]
    except IndexError:
        print("Ultrapassou o número de círculos")
    try:
        C[3] = [10,4.5]
    except IndexError:
        print("Ultrapassou o número de círculos")
    try:
        C[4] = [-12,12.5]
    except IndexError:
        print("Ultrapassou o número de círculos")


    for icir in range(n_circles):
        cx = C[icir, 0]
        cy = C[icir, 1]
        r = radius_max*np.random.rand(n_dots_per_circle)
        theta = np.random.rand(n_dots_per_circle)

        X[icir*n_dots_per_circle:(icir+1)*n_dots_per_circle, 0] = cx + r*np.cos(2*np.pi*theta)
        X[icir*n_dots_per_circle:(icir+1)*n_dots_per_circle, 1] = cy + r*np.sin(2*np.pi*theta)
    return X



def cluster(X, eps = 1.0, min_samples = 6):
    '''
    Use DBSCAN algorithm to cluster the different oil stains
    
    returns: ndarray of categorized particles 
    '''
    clustering_dbscan = DBSCAN(eps = eps, min_samples = min_samples).fit(X)

    X_labels = clustering_dbscan.labels_

    return X_labels




def separation(X, X_labels):
    '''
    Separates each coordinates particles according to their clustering type

    returns: dict of (ndarray of coordinates of the particles)
    '''

    cluster_dict = {}

    labels = np.unique(X_labels)
    labels = labels[labels != -1]

    for n in labels:
        cluster_dict[f'{n}'] = X[X_labels == n]

    return cluster_dict





def polygondata(cluster_dico):
    '''
    Use the ConvexHull algorithm to get the border points of the different oil stains

    returns: dict of (ndarray of coordinates of the vertices from each cluster)
    '''
    vertices_dict = {} #Coordenadas dos vertices

    for cluster_nb, points in cluster_dico.items():
        hull = ConvexHull(points)
        vertices_dict[cluster_nb] = points[hull.vertices]

    return vertices_dict




### TRANSFORM VERTICES COORDINATES INTO INDICES ###
def minborders(vert_dict):
    '''
    Gets the lowest and the leftmost coordinates of the whole vertices set to define the frame

    returns: 2 integers
    '''

    xmin = np.inf
    ymin = np.inf
    for clusterverts in vert_dict.values():
        xmin = min(xmin, np.min(clusterverts[:, 0]))
        ymin = min(ymin, np.min(clusterverts[:, 1]))
    return xmin, ymin


def coord2index(vert_dict, step):
    '''
    Transforms the coordinates of each clusters' vertex into indices (or pixels) for the raw matrix

    step: matrix resolution. The lower the better the resolution is

    returns: dict of the indices for the matrix
    '''
    ind_vert_matrix = {}
    xmin, ymin = minborders(vert_dict)

    for key, coords in vert_dict.items():
        ind_coords = np.zeros(coords.shape, dtype=int)
        for idx, (x, y) in enumerate(coords):
            i = int(np.ceil((x - xmin) / step))
            j = int(np.ceil((y - ymin) / step))
            ind_coords[idx] = [i, j]
        ind_vert_matrix[key] = ind_coords

    return ind_vert_matrix


def maxborder(ind_vert_matrix):
    '''
    Defines the minimum size (in pixels) of the matrix

    returns: horizontal and vertical greatest pixels (2 integers)

    '''
    imax = 0
    jmax = 0

    for vert_indices in ind_vert_matrix.values():
        imax = max(imax, np.max(vert_indices[:, 0]))
        jmax = max(jmax, np.max(vert_indices[:, 1]))
    
    return imax, jmax




def blackwhitematrix(vert_dict, padding_rate=0.05, step=0.05):
    '''
    Creates the matrix using polygon function to fulfill the interior of the oil stains

    Readjust the size of the matrix  using a padding rate which acts as a zoom out

    returns: ndarray
    '''
    if padding_rate >= 0.5:
        print("Cuidado, padding_rate deve ficar em [0 ; 0.5[")
        print("Padding zerado ...")
        padding_rate = 0

    ind_vert_matrix = coord2index(vert_dict, step)
    datasizex, datasizey = maxborder(ind_vert_matrix)


    framesizex = int(datasizex / (1-2*padding_rate))
    framesizey = int(datasizey / (1-2*padding_rate))


    bwmatrix = np.zeros((framesizex + 1, framesizey + 1))

    for _, vert_indices in ind_vert_matrix.items():
        rr, cc = polygon(vert_indices[:, 0], vert_indices[:, 1])
        bwmatrix[int(padding_rate*framesizex) + rr, int(padding_rate*framesizey) + cc] = 1

    return bwmatrix



def visual(dados, cluster_dados, bwmatrix):
    '''
    Allows to visualize the oil data and the corresponding matrix
    '''
    labels = np.unique(cluster_dados)
    labels = labels[labels != -1]  # remove noise
    nclusters = len(labels)

    f, (ax1, ax2) = plt.subplots(1, 2)
    ax1.scatter(dados[:, 0], dados[:, 1], c=cluster_dados)
    ax1.set_title(f"DBSCAN (reconheceu {nclusters} clusters)")
    ax1.set_aspect('equal', 'box')

    ax2.imshow(np.rot90(bwmatrix), cmap='gray')
    ax2.set_title("Black & white matrix")
    ax2.set_aspect('equal', 'box')
    plt.show()