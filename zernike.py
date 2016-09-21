# zernike.py
"""
A module defining the zernike polynomials and associated functions to convert
between radial and azimuthal degree pairs and Noll's indices.

Running this file as a scrip will output a graph of the first 15 zernike
polynomials on the unit disk.

https://en.wikipedia.org/wiki/Zernike_polynomials
"""

import numpy as np
from scipy.special import binom, hyp2f1
from .utils import cart2pol

# forward mapping of Noll indices
noll_mapping = np.array([
    1, 3, 2, 5, 4, 6, 9, 7, 8, 10, 15, 13, 11, 12, 14, 21, 19, 17, 16,
    18, 20, 27, 25, 23, 22, 24, 26, 28, 35, 33, 31, 29, 30, 32, 34,
    36, 45, 43, 41, 39, 37, 38, 40, 42, 44, 55, 53, 51, 49, 47, 46,
    48, 50, 52, 54, 65, 63, 61, 59, 57, 56, 58, 60, 62, 64, 66, 77,
    75, 73, 71, 69, 67, 68, 70, 72, 74, 76, 78, 91, 89, 87, 85, 83,
    81, 79, 80, 82, 84, 86, 88, 90, 105, 103, 101, 99, 97, 95, 93,
    92, 94, 96, 98, 100, 102, 104, 119, 117, 115, 113, 111, 109,
    107, 106, 108, 110, 112, 114, 116, 118, 120
])

# reverse mapping of noll indices
noll_inverse = noll_mapping.argsort()

# classical names for the Noll indices
# https://en.wikipedia.org/wiki/Zernike_polynomials
noll2name = {
    1: "Piston",
    2: "Tip (lateral position) (X-Tilt)",
    3: "Tilt (lateral position) (Y-Tilt)",
    4: "Defocus (longitudinal position)",
    5: "Oblique astigmatism",
    6: "Vertical astigmatism",
    7: "Vertical coma",
    8: "Horizontal coma",
    9: "Vertical trefoil",
    10: "Oblique trefoil",
    11: "Primary spherical",
    12: "Vertical secondary astigmatism",
    13: "Oblique secondary astigmatism",
    14: "Vertical quadrafoil",
    15: "Oblique quadrafoil"
}


def noll2degrees(noll):
    """Convert from Noll's indices to radial degree and azimuthal degree"""
    noll = np.asarray(noll)
    if not np.issubdtype(noll.dtype, int):
        raise ValueError("input is not integer, input = {}".format(noll))
    if not (noll > 0).all():
        raise ValueError(
            "Noll indices must be greater than 0, input = {}".format(noll))
    # need to subtract 1 from the Noll's indices because they start at 1.
    p = noll_inverse[noll - 1]
    n = np.ceil((-3 + np.sqrt(9 + 8 * p)) / 2)
    m = 2 * p - n * (n + 2)
    return n.astype(int), m.astype(int)


def degrees2noll(n, m):
    """Convert from radial and azimuthal degrees to Noll's index"""
    n, m = np.asarray(n), np.asarray(m)
    # check inputs
    if not np.issubdtype(n.dtype, int):
        raise ValueError(
            "Radial degree is not integer, input = {}".format(n))
    if not np.issubdtype(m.dtype, int):
        raise ValueError(
            "Azimuthal degree is not integer, input = {}".format(m))
    if ((n - m) % 2).any():
        raise ValueError(
            "The difference between radial and azimuthal degree isn't mod 2")
    # do the mapping
    p = (m + n * (n + 2)) / 2
    noll = noll_mapping[p.astype(int)]
    return noll


def zernike(r, theta, *args, **kwargs):
    """Calculates the Zernike polynomial on the unit disk or the requested
    orders

    Parameters
    ----------
    r : ndarray
    theta : ndarray

    Args
    ----
    Noll : numeric or numeric sequence
        Noll's Indices to generate
    (n, m) : tuple of numerics or numeric sequences
        Radial and azimuthal degrees
    n : see above
    m : see above

    Kwargs
    ------
    norm : bool (default False)
        Do you want the output normed?

    Returns
    -------
    zernike : ndarray
        The zernike polynomials corresponding to Noll or (n, m) whichever are
        provided

    Example
    -------
    >>> x = np.linspace(-1, 1, 512)
    >>> xx, yy = np.meshgrid(x, x)
    >>> r, theta = cart2pol(yy, xx)
    >>> zern = zernike(r, theta, 4)  # generates the defocus zernike polynomial
    """
    if len(args) == 1:
        args = np.asarray(args[0])
        if args.ndim < 2:
            n, m = noll2degrees(args)
        elif args.ndim == 2:
            if args.shape[0] == 2:
                n, m = args
            else:
                raise RuntimeError("This shouldn't happen")
        else:
            raise ValueError("{} is the wrong shape".format(args.shape))
    elif len(args) == 2:
        n, m = np.asarray(args)
        if n.ndim > 1:
            raise ValueError("Radial degree has the wrong shape")
        if m.ndim > 1:
            raise ValueError("Azimuthal degree has the wrong shape")
        if n.shape != m.shape:
            raise ValueError(
                "Radial and Azimuthal degrees have different shapes")
    else:
        raise ValueError(
            "{} is an invalid number of arguments".format(len(args)))
    # make sure r and theta are arrays
    r = np.asarray(r)
    theta = np.asarray(theta)
    if r.ndim > 2:
        raise ValueError(
            "Input rho and theta cannot have more than two dimensions")
    # make sure that n and m are iterable
    n, m = n.ravel(), m.ravel()
    # return column of zernike polynomials
    return np.array([_zernike(r, theta, nn, mm, **kwargs)
                     for nn, mm in zip(n, m)]).squeeze()


def _radial_zernike(r, n, m):
    """The radial part of the zernike polynomial"""
    rad_zern = np.zeros_like(r)
    # zernike polynomials are only valid for r <= 1
    valid_points = r <= 1.0
    if m == 0 and n == 0:
        rad_zern[valid_points] = 1
        return rad_zern
    rprime = r[valid_points]
    rn = rprime ** n
    bincoef = binom(n, (n + m) // 2)
    hyper = hyp2f1(-(n + m) // 2, -(n - m) // 2, -n, rprime**(-2))
    rad_zern[valid_points] = bincoef * rn * hyper
    return rad_zern


def _zernike(r, theta, n, m, norm=True):
    """The actual function that calculates the full zernike polynomial"""
    # if m and n aren't seperated by two then return zeros
    if (m - n) % 2:
        return np.zeros_like(r)
    zern = _radial_zernike(r, n, m)
    if m < 0:
        # odd zernike
        zern *= np.sin(m * theta)
    else:
        # even zernike
        zern *= np.cos(m * theta)
    # calculate the normalization factor
    if norm:
        zern /= np.linalg.norm(zern.ravel())
    return zern


if __name__ == "__main__":
    from matplotlib import pyplot as plt
    # make coordinates
    x = np.linspace(-1, 1, 512)
    xx, yy = np.meshgrid(x, x)  # xy indexing is default
    r, theta = cart2pol(yy, xx)
    # set up plot
    fig, axs = plt.subplots(3, 5, figsize=(15, 9))
    # fill out plot
    for ax, (k, v) in zip(axs.ravel(), noll2name.items()):
        zern = zernike(r, theta, k, norm=False)
        ax.matshow(zern, vmin=-1, vmax=1, cmap="coolwarm")
        ax.set_title(v)
        ax.axis("off")
    fig.tight_layout()
    plt.show()
