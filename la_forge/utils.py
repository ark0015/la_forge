import glob
import numpy as np
import scipy.interpolate as interp
import scipy.ndimage.filters as filter

try:
    from enterprise.pulsar import Pulsar
    ent_present = True
except ImportError:
    ent_present = False


fyr = 1./31536000.


# from Kristina

def getMax2d(samples1, samples2, weights=None, smooth=True, bins=[40, 40],
            x_range=None, y_range=None, logx=False, logy=False, logz=False):
    """ Function to return the maximum likelihood values by interpolating over
    a two dimensional histogram made of two sets of samples.

    Parameters
    ----------

    samples1, samples2 : array or list
        Arrays or lists from which to find two dimensional maximum likelihood
        values.

    weights : array of floats
        Weights to use in histogram.

    bins : list of ints
        List of 2 integers which dictates number of bins for samples1 and
        samples2.

    x_range : tuple, optional
        Range of samples1

    y_range : tuple, optional
        Range of samples2

    logx : bool, optional
        A value of True use log10 scale for samples1.

    logy : bool, optional
        A value of True use log10 scale for samples2.

    logz : bool, optional
        A value of True indicates that the z axis is in log10.

    """

    if x_range is None:
        xmin = np.amin(samples1)
        xmax = np.amax(samples1)
    else:
        xmin = x_range[0]
        xmax = x_range[1]

    if y_range is None:
        ymin = np.amin(samples2)
        ymax = np.amax(samples2)
    else:
        ymin = y_range[0]
        ymax = y_range[1]

    if logx:
        bins[0] = np.logspace(np.log10(xmin), np.log10(xmax), bins[0])

    if logy:
        bins[1] = np.logspace(np.log10(ymin), np.log10(ymax), bins[1])

    hist2d,xedges,yedges = np.histogram2d(samples1, samples2, weights=weights,
                                          bins=bins,
                                          range=[[xmin,xmax],[ymin,ymax]])
    extent = [xedges[0], xedges[-1], yedges[0], yedges[-1] ]

    if logz:
        hist2d = np.where(hist2d >= 0,hist2d,1)

    xedges = np.delete(xedges, -1) + 0.5*(xedges[1] - xedges[0])
    yedges = np.delete(yedges, -1) + 0.5*(yedges[1] - yedges[0])

    # gaussian smoothing
    if smooth:
        hist2d = filter.gaussian_filter(hist2d, sigma=0.75)

    # interpolation
    f = interp.interp2d(xedges, yedges, hist2d, kind='cubic')
    xedges = np.linspace(xedges.min(), xedges.max(), 10000)
    yedges = np.linspace(yedges.min(), yedges.max(), 10000)
    hist2d = f(xedges, yedges)

    # return xedges[np.argmax(hist2d)]
    ind = np.unravel_index(np.argmax(hist2d), hist2d.shape)
    return xedges[ind[0]], yedges[ind[1]]


def get_noise_params_2d_mlv(core, par1, par2):
    """Convenience function for finding two dimensional maximum likelihood
    value for any two parameters.
    """

    samps1 = core.get_param(par1, to_burn=True)
    samps2 = core.get_param(par2, to_burn=True)

    return getMax2d(samps1,samps2)

def get_rn_noise_params_2d_mlv(core, pulsar):
    """Convenience function to find 2d rednoise maximum likelihood values.
    """
    rn_si = pulsar + '_gamma'
    rn_amp = pulsar + '_log10_A'

    return get_noise_params_2d_mlv(rn_si,rn_amp)

def get_Tspan(pulsar, datadir):
    """Returns timespan of a pulsars dataset by loading the pulsar as an
    `enterprise.Pulsar()` object.

    Parameters
    ----------
    pulsar : str

    datadir : str
        Directory where `par` and `tim` files are found.
    """
    if not ent_present:
        raise ImportError('enterprise is not available for import. '
                          'Please provide time span of data in another form.')
    parfile = glob.glob(datadir + '/{0}*.par'.format(pulsar))[0]
    timfile = glob.glob(datadir + '/{0}*.tim'.format(pulsar))[0]

    psr = Pulsar(parfile, timfile, ephem='{0}'.format('DE436'))

    T = psr.toas.max() - psr.toas.min()

    return T



def compute_rho(log10_A, gamma, f, T):
    """
    Converts from power to residual RMS.
    """

    return np.sqrt((10**log10_A)**2 / (12.0*np.pi**2) * fyr**(gamma-3) * f**(-gamma) / T)
