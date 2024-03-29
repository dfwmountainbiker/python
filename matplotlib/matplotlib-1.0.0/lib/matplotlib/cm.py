"""
This module provides a large set of colormaps, functions for
registering new colormaps and for getting a colormap by name,
and a mixin class for adding color mapping functionality.

"""

import os

import numpy as np
from numpy import ma
import matplotlib as mpl
import matplotlib.colors as colors
import matplotlib.cbook as cbook
from matplotlib._cm import datad

cmap_d = dict()

# reverse all the colormaps.
# reversed colormaps have '_r' appended to the name.

def _reverser(f):
    def freversed(x):
        return f(1-x)
    return freversed

def revcmap(data):
    data_r = {}
    for key, val in data.iteritems():
        if callable(val):
            valnew = _reverser(val)
                # This doesn't work: lambda x: val(1-x)
                # The same "val" (the first one) is used
                # each time, so the colors are identical
                # and the result is shades of gray.
        else:
            valnew = [(1.0 - a, b, c) for a, b, c in reversed(val)]
        data_r[key] = valnew
    return data_r

LUTSIZE = mpl.rcParams['image.lut']

_cmapnames = datad.keys()  # need this list because datad is changed in loop

for cmapname in _cmapnames:
    cmapname_r = cmapname+'_r'
    cmapspec = datad[cmapname]
    if 'red' in cmapspec:
        datad[cmapname_r] = revcmap(cmapspec)
        cmap_d[cmapname] = colors.LinearSegmentedColormap(
                                cmapname, cmapspec, LUTSIZE)
        cmap_d[cmapname_r] = colors.LinearSegmentedColormap(
                                cmapname_r, datad[cmapname_r], LUTSIZE)
    else:
        revspec = list(reversed(cmapspec))
        if len(revspec[0]) == 2:    # e.g., (1, (1.0, 0.0, 1.0))
            revspec = [(1.0 - a, b) for a, b in revspec]
        datad[cmapname_r] = revspec

        cmap_d[cmapname] = colors.LinearSegmentedColormap.from_list(
                                cmapname, cmapspec, LUTSIZE)
        cmap_d[cmapname_r] = colors.LinearSegmentedColormap.from_list(
                                cmapname_r, revspec, LUTSIZE)

locals().update(cmap_d)

def register_cmap(name=None, cmap=None, data=None, lut=None):
    """
    Add a colormap to the set recognized by :func:`get_cmap`.

    It can be used in two ways::

        register_cmap(name='swirly', cmap=swirly_cmap)

        register_cmap(name='choppy', data=choppydata, lut=128)

    In the first case, *cmap* must be a :class:`colors.Colormap`
    instance.  The *name* is optional; if absent, the name will
    be the :attr:`name` attribute of the *cmap*.

    In the second case, the three arguments are passed to
    the :class:`colors.LinearSegmentedColormap` initializer,
    and the resulting colormap is registered.

    """
    if name is None:
        try:
            name = cmap.name
        except AttributeError:
            raise ValueError("Arguments must include a name or a Colormap")

    if not cbook.is_string_like(name):
        raise ValueError("Colormap name must be a string")

    if isinstance(cmap, colors.Colormap):
        cmap_d[name] = cmap
        return

    # For the remainder, let exceptions propagate.
    if lut is None:
        lut = mpl.rcParams['image.lut']
    cmap = colors.LinearSegmentedColormap(name, data, lut)
    cmap_d[name] = cmap

def get_cmap(name=None, lut=None):
    """
    Get a colormap instance, defaulting to rc values if *name* is None.

    Colormaps added with :func:`register_cmap` take precedence over
    builtin colormaps.

    If *name* is a :class:`colors.Colormap` instance, it will be
    returned.

    If *lut* is not None it must be an integer giving the number of
    entries desired in the lookup table, and *name* must be a
    standard mpl colormap name with a corresponding data dictionary
    in *datad*.
    """
    if name is None:
        name = mpl.rcParams['image.cmap']

    if isinstance(name, colors.Colormap):
        return name

    if name in cmap_d:
        if lut is None:
            return cmap_d[name]
        elif name in datad:
            return colors.LinearSegmentedColormap(name,  datad[name], lut)
        else:
            raise ValueError("Colormap %s is not recognized" % name)

class ScalarMappable:
    """
    This is a mixin class to support scalar -> RGBA mapping.  Handles
    normalization and colormapping
    """

    def __init__(self, norm=None, cmap=None):
        """
        *norm* is an instance of :class:`colors.Normalize` or one of
        its subclasses, used to map luminance to 0-1. *cmap* is a
        :mod:`cm` colormap instance, for example :data:`cm.jet`
        """

        self.callbacksSM = cbook.CallbackRegistry((
                'changed',))

        if cmap is None: cmap = get_cmap()
        if norm is None: norm = colors.Normalize()

        self._A = None
        self.norm = norm
        self.cmap = get_cmap(cmap)
        self.colorbar = None
        self.update_dict = {'array':False}

    def set_colorbar(self, im, ax):
        'set the colorbar image and axes associated with mappable'
        self.colorbar = im, ax

    def to_rgba(self, x, alpha=None, bytes=False):
        '''Return a normalized rgba array corresponding to *x*. If *x*
        is already an rgb array, insert *alpha*; if it is already
        rgba, return it unchanged. If *bytes* is True, return rgba as
        4 uint8s instead of 4 floats.
        '''
        if alpha is None:
            _alpha = 1.0
        else:
            _alpha = alpha
        try:
            if x.ndim == 3:
                if x.shape[2] == 3:
                    if x.dtype == np.uint8:
                        _alpha = np.array(_alpha*255, np.uint8)
                    m, n = x.shape[:2]
                    xx = np.empty(shape=(m,n,4), dtype = x.dtype)
                    xx[:,:,:3] = x
                    xx[:,:,3] = _alpha
                elif x.shape[2] == 4:
                    xx = x
                else:
                    raise ValueError("third dimension must be 3 or 4")
                if bytes and xx.dtype != np.uint8:
                    xx = (xx * 255).astype(np.uint8)
                return xx
        except AttributeError:
            pass
        x = ma.asarray(x)
        x = self.norm(x)
        x = self.cmap(x, alpha=alpha, bytes=bytes)
        return x

    def set_array(self, A):
        'Set the image array from numpy array *A*'
        self._A = A
        self.update_dict['array'] = True

    def get_array(self):
        'Return the array'
        return self._A

    def get_cmap(self):
        'return the colormap'
        return self.cmap

    def get_clim(self):
        'return the min, max of the color limits for image scaling'
        return self.norm.vmin, self.norm.vmax

    def set_clim(self, vmin=None, vmax=None):
        """
        set the norm limits for image scaling; if *vmin* is a length2
        sequence, interpret it as ``(vmin, vmax)`` which is used to
        support setp

        ACCEPTS: a length 2 sequence of floats
        """
        if (vmin is not None and vmax is None and
                                cbook.iterable(vmin) and len(vmin)==2):
            vmin, vmax = vmin

        if vmin is not None: self.norm.vmin = vmin
        if vmax is not None: self.norm.vmax = vmax
        self.changed()

    def set_cmap(self, cmap):
        """
        set the colormap for luminance data

        ACCEPTS: a colormap or registered colormap name
        """
        cmap = get_cmap(cmap)
        self.cmap = cmap
        self.changed()

    def set_norm(self, norm):
        'set the normalization instance'
        if norm is None: norm = colors.Normalize()
        self.norm = norm
        self.changed()

    def autoscale(self):
        """
        Autoscale the scalar limits on the norm instance using the
        current array
        """
        if self._A is None:
            raise TypeError('You must first set_array for mappable')
        self.norm.autoscale(self._A)
        self.changed()

    def autoscale_None(self):
        """
        Autoscale the scalar limits on the norm instance using the
        current array, changing only limits that are None
        """
        if self._A is None:
            raise TypeError('You must first set_array for mappable')
        self.norm.autoscale_None(self._A)
        self.changed()


    def add_checker(self, checker):
        """
        Add an entry to a dictionary of boolean flags
        that are set to True when the mappable is changed.
        """
        self.update_dict[checker] = False

    def check_update(self, checker):
        """
        If mappable has changed since the last check,
        return True; else return False
        """
        if self.update_dict[checker]:
            self.update_dict[checker] = False
            return True
        return False

    def changed(self):
        """
        Call this whenever the mappable is changed to notify all the
        callbackSM listeners to the 'changed' signal
        """
        self.callbacksSM.process('changed', self)

        for key in self.update_dict:
            self.update_dict[key] = True
