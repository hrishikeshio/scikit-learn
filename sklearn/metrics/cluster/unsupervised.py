""" Unsupervised evaluation metrics. """

# Authors: Robert Layton <robertlayton@gmail.com>
#
# License: BSD Style.

import numpy as np

from ...utils import check_random_state
from ..pairwise import pairwise_distances


def silhouette_score(X, classes, labels=None, metric='euclidean',
                     sample_size=None, random_state=None, **kwds):
    """Compute the mean Silhouette Coefficient of all samples.

    The Silhouette Coefficient is calculated using the mean intra-cluster
    distance (``a``) and the mean nearest-cluster distance (``b``) for each
    sample.  The Silhouette Coefficient for a sample is ``(b - a) / max(a,
    b)``.  To clarify, ``b`` is the distance between a sample and the nearest
    cluster that the sample is not a part of.

    This function returns the mean Silhouette Coefficient over all samples.
    To obtain the values for each sample, use :func:`silhouette_samples`.

    The best value is 1 and the worst value is -1. Values near 0 indicate
    overlapping clusters. Negative values generally indicate that a sample has
    been assigned to the wrong cluster, as a different cluster is more similar.

    Parameters
    ----------
    X : array [n_samples_a, n_samples_a] if metric == "precomputed", or, \
             [n_samples_a, n_features] otherwise
        Array of pairwise distances between samples, or a feature array.

    classes : array, shape = [n_samples]
             class values for each sample

    metric : string, or callable
        The metric to use when calculating distance between instances in a
        feature array. If metric is a string, it must be one of the options
        allowed by :func:`metrics.pairwise.pairwise_distances
        <sklearn.metrics.pairwise.pairwise_distances>`. If X is the distance
        array itself, use ``metric="precomputed"``.

    sample_size : int or None
        The size of the sample to use when computing the Silhouette
        Coefficient. If ``sample_size is None``, no sampling is used.

    random_state : integer or numpy.RandomState, optional
        The generator used to initialize the centers. If an integer is
        given, it fixes the seed. Defaults to the global numpy random
        number generator.

    `**kwds` : optional keyword parameters
        Any further parameters are passed directly to the distance function.
        If using a scipy.spatial.distance metric, the parameters are still
        metric dependent. See the scipy docs for usage examples.

    Returns
    -------
    silhouette : float
        Mean Silhouette Coefficient for all samples.

    References
    ----------

    .. [1] `Peter J. Rousseeuw (1987). "Silhouettes: a Graphical Aid to the
       Interpretation and Validation of Cluster Analysis". Computational
       and Applied Mathematics 20: 53-65.
       <http://www.sciencedirect.com/science/article/pii/0377042787901257>`_

    .. [2] `Wikipedia entry on the Silhouette Coefficient
           <http://en.wikipedia.org/wiki/Silhouette_(clustering)>`_

    """
    if labels is not None:
        warnings.warn("Parameter 'labels' is deprecated and will be "
                      "removed in 0.15. Please use 'classes' instead",
                      DeprecationWarning)
        classes = labels

    if sample_size is not None:
        random_state = check_random_state(random_state)
        indices = random_state.permutation(X.shape[0])[:sample_size]
        if metric == "precomputed":
            X, classes = X[indices].T[indices].T, classes[indices]
        else:
            X, classes = X[indices], classes[indices]
    return np.mean(silhouette_samples(X, classes, metric=metric, **kwds))


def silhouette_samples(X, classes, labels=None, metric='euclidean', **kwds):
    """Compute the Silhouette Coefficient for each sample.

    The Silhoeutte Coefficient is a measure of how well samples are clustered
    with samples that are similar to themselves. Clustering models with a high
    Silhouette Coefficient are said to be dense, where samples in the same
    cluster are similar to each other, and well separated, where samples in
    different clusters are not very similar to each other.

    The Silhouette Coefficient is calculated using the mean intra-cluster
    distance (``a``) and the mean nearest-cluster distance (``b``) for each
    sample.  The Silhouette Coefficient for a sample is ``(b - a) / max(a,
    b)``.

    This function returns the Silhouette Coefficient for each sample.

    The best value is 1 and the worst value is -1. Values near 0 indicate
    overlapping clusters.

    Parameters
    ----------
    X : array [n_samples_a, n_samples_a] if metric == "precomputed", or, \
             [n_samples_a, n_features] otherwise
        Array of pairwise distances between samples, or a feature array.

    classes : array, shape = [n_samples]
             class values for each sample

    metric : string, or callable
        The metric to use when calculating distance between instances in a
        feature array. If metric is a string, it must be one of the options
        allowed by :func:`sklearn.metrics.pairwise.pairwise_distances`. If X is
        the distance array itself, use "precomputed" as the metric.

    `**kwds` : optional keyword parameters
        Any further parameters are passed directly to the distance function.
        If using a ``scipy.spatial.distance`` metric, the parameters are still
        metric dependent. See the scipy docs for usage examples.

    Returns
    -------
    silhouette : array, shape = [n_samples]
        Silhouette Coefficient for each samples.

    References
    ----------

    .. [1] `Peter J. Rousseeuw (1987). "Silhouettes: a Graphical Aid to the
       Interpretation and Validation of Cluster Analysis". Computational
       and Applied Mathematics 20: 53-65.
       <http://www.sciencedirect.com/science/article/pii/0377042787901257>`_

    .. [2] `Wikipedia entry on the Silhouette Coefficient
       <http://en.wikipedia.org/wiki/Silhouette_(clustering)>`_

    """

    if labels is not None:
        warnings.warn("Parameter 'labels' is deprecated and will"
                      " be removed in 0.15. Please use 'classes' instead",
                      DeprecationWarning)
        classes = labels

    distances = pairwise_distances(X, metric=metric, **kwds)
    n = classes.shape[0]
    A = np.array([_intra_cluster_distance(distances[i], classes, i)
                  for i in range(n)])
    B = np.array([_nearest_cluster_distance(distances[i], classes, i)
                  for i in range(n)])
    sil_samples = (B - A) / np.maximum(A, B)
    # nan values are for clusters of size 1, and should be 0
    return np.nan_to_num(sil_samples)


def _intra_cluster_distance(distances_row, classes, i, labels=None):
    """Calculate the mean intra-cluster distance for sample i.

    Parameters
    ----------
    distances_row : array, shape = [n_samples]
        Pairwise distance matrix between sample i and each sample.

    classes : array, shape = [n_samples]
        class values for each sample

    i : int
        Sample index being calculated. It is excluded from calculation and
        used to determine the current class

    Returns
    -------
    a : float
        Mean intra-cluster distance for sample i
    """

    if labels is not None:
        warnings.warn("Parameter 'labels' is deprecated"
                      " and will be removed in 0.15. "
                      "Please use 'classes' instead",
                      DeprecationWarning)
        classes = labels

    mask = classes == classes[i]
    mask[i] = False
    a = np.mean(distances_row[mask])
    return a


def _nearest_cluster_distance(distances_row, classes, i, labels=None):
    """Calculate the mean nearest-cluster distance for sample i.

    Parameters
    ----------
    distances_row : array, shape = [n_samples]
        Pairwise distance matrix between sample i and each sample.

    classes : array, shape = [n_samples]
        class values for each sample

    i : int
        Sample index being calculated. It is used to determine the current
        class.

    Returns
    -------
    b : float
        Mean nearest-cluster distance for sample i
    """
    class_ = classes[i]
    b = np.min([np.mean(distances_row[classes == cur_class])
               for cur_class in set(classes) if not cur_class == class_])
    return b
