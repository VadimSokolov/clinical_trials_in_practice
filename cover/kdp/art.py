#!/usr/bin/env python3
"""Draws the art of the front cover of Clinical Trials in Practice: two Kaplan-Meier curves with their confidence bands.

The curves are the product-limit estimates of two simulated arms (the seed is below), with the Greenwood bands and the
censoring marks of a real survival plot. There is no image model and no photograph in it: the page is drawn from code.
Writes art.png, the size of the front panel with its bleed (7.125 x 10.25 in) at 400 ppi, without any text. The title, the
subtitle and the authors are typeset over it as vector text by cover.tex, which also draws the spine and the back.

    python3 art.py [--ppi 400] [--out art.png]

Needs numpy, scipy, matplotlib and Pillow; at 400 ppi it takes about a minute. The wrap is then built with pdflatex (see cover.tex).
"""
import argparse

import matplotlib
import numpy as np

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter

W_IN, H_IN = 7.125, 10.25                      # the front panel with the 0.125 in bleed on the right, the top and the bottom
NAVY = np.array([11, 30, 58]) / 255            # the ground of the whole wrap (cover.tex uses the same color)
TEAL = np.array([60, 198, 181]) / 255          # the treatment arm
AMBER = np.array([246, 178, 107]) / 255        # the control arm
ORANGE = np.array([255, 140, 58]) / 255        # its bands, more saturated so that they do not turn gray over the navy ground
TEAL_BAND = np.array([40, 190, 178]) / 255
MIST = np.array([196, 210, 230]) / 255         # axes and guides
X0, X1 = 0.75, 7.95                            # time 0 and time T on the page, in inches; the curves run off the right edge
Y0, Y1 = 1.95, 6.60                            # survival 0 and 1 on the page
T = 42.0                                       # months
SEED = 11
RATES = (0.022, 0.065)                          # monthly hazard of the treatment and the control arm
BAND, EDGE = 0.12, 0.45                        # opacity of the confidence bands and of their outlines
MEDIANS = True                                 # dashed lines at the median survival of each arm


def simulate(rng, n, rate, censor_rate):
    """Exponential event times, random censoring and administrative censoring at T."""
    event = rng.exponential(1 / rate, n)
    cens = np.minimum(rng.exponential(1 / censor_rate, n), T)
    return np.minimum(event, cens), event <= cens


def kaplan_meier(t, d):
    """Product-limit estimate with Greenwood intervals: step times, survival, lower, upper, and the censoring marks."""
    order = np.argsort(t, kind='stable')
    t, d = t[order], d[order]
    at_risk, s, green = len(t), 1.0, 0.0
    xs, ss, lo, hi, marks = [0.0], [1.0], [1.0], [1.0], []
    for ti, di in zip(t, d):
        if di and at_risk > 1:
            s *= 1 - 1 / at_risk
            green += 1 / (at_risk * (at_risk - 1))
            se = s * np.sqrt(green)
            xs.append(ti), ss.append(s), lo.append(max(0.0, s - 1.96 * se)), hi.append(min(1.0, s + 1.96 * se))
        elif not di:
            marks.append((ti, s))
        at_risk -= 1
    xs.append(T), ss.append(ss[-1]), lo.append(lo[-1]), hi.append(hi[-1])
    return np.array(xs), np.array(ss), np.array(lo), np.array(hi), np.array(marks)


def px(x, y):
    """Page inches to the axes of the layer."""
    return X0 + np.asarray(x) * (X1 - X0) / T, Y0 + np.asarray(y) * (Y1 - Y0)


def layer(ppi, draw):
    """Draws one transparent layer at the page size and returns it as straight RGBA floats."""
    fig = plt.figure(figsize=(W_IN, H_IN), dpi=ppi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W_IN), ax.set_ylim(0, H_IN), ax.axis('off')
    fig.patch.set_alpha(0)
    draw(ax)
    fig.canvas.draw()
    out = np.asarray(fig.canvas.buffer_rgba()).astype(np.float32) / 255
    plt.close(fig)
    return out


def screen(base, rgba, opacity=1.0):
    a = rgba[..., 3:4] * opacity
    return 1 - (1 - base) * (1 - rgba[..., :3] * a)


def over(base, rgba, opacity=1.0):
    a = rgba[..., 3:4] * opacity
    return base * (1 - a) + rgba[..., :3] * a


def main():
    global BAND, EDGE, MEDIANS, AMBER
    ap = argparse.ArgumentParser()
    ap.add_argument('--ppi', type=int, default=400)
    ap.add_argument('--out', default='art.png')
    ap.add_argument('--band', type=float, default=BAND)
    ap.add_argument('--edge', type=float, default=EDGE)
    ap.add_argument('--control', default='amber', help='amber, mist or coral')
    ap.add_argument('--no-medians', action='store_true')
    a = ap.parse_args()
    ppi = a.ppi
    BAND, EDGE, MEDIANS = a.band, a.edge, not a.no_medians
    AMBER = {'amber': AMBER, 'mist': np.array([214, 226, 242]) / 255, 'coral': np.array([255, 128, 106]) / 255}[a.control]
    inch = ppi                                           # pixels per inch, for blur radii
    rng = np.random.default_rng(SEED)
    arms = [(TEAL, kaplan_meier(*simulate(rng, 52, RATES[0], 0.012))),
            (AMBER, kaplan_meier(*simulate(rng, 52, RATES[1], 0.012)))]
    h, w = round(H_IN * ppi), round(W_IN * ppi)
    img = np.ones((h, w, 3), np.float32) * NAVY.astype(np.float32)
    pt = 72                                              # points per inch

    def bands(ax):
        for color, (xs, ss, lo, hi, marks) in arms:
            x, ylo = px(xs, lo)
            yhi = px(xs, hi)[1]
            bc = ORANGE if color is AMBER else TEAL_BAND if color is TEAL else color
            ax.fill_between(x, ylo, yhi, step='post', color=bc, alpha=BAND, lw=0)
            if EDGE:
                for y in (ylo, yhi):
                    ax.step(x, y, where='post', color=bc, alpha=EDGE, lw=0.012 * pt, solid_joinstyle='miter')

    def curves(ax, lw=0.058, marks=True):
        for color, (xs, ss, lo, hi, m) in arms:
            x, y = px(xs, ss)
            ax.step(x, y, where='post', color=color, lw=lw * pt, solid_joinstyle='round', solid_capstyle='round')
            if marks and len(m):
                mx, my = px(m[:, 0], m[:, 1])
                for u, v in zip(mx, my):
                    ax.plot([u, u], [v - 0.095, v + 0.095], color=color, lw=0.026 * pt, solid_capstyle='butt')

    def axes_guides(ax):
        c = tuple(MIST) + (0.38,)
        ax.plot([X0, W_IN], [Y0, Y0], color=c, lw=0.011 * pt, solid_capstyle='butt')
        ax.plot([X0, X0], [Y0, Y1 + 0.2], color=c, lw=0.011 * pt, solid_capstyle='butt')
        for s in (0, 0.25, 0.5, 0.75, 1.0):
            y = px(0, s)[1]
            ax.plot([X0 - 0.09, X0], [y, y], color=c, lw=0.011 * pt, solid_capstyle='butt')
        for t in range(0, 42, 6):
            x = px(t, 0)[0]
            if x < W_IN - 0.1:
                ax.plot([x, x], [Y0 - 0.09, Y0], color=c, lw=0.011 * pt, solid_capstyle='butt')

    def medians(ax):
        for color, (xs, ss, lo, hi, m) in arms:
            t50 = xs[np.argmax(ss <= 0.5)]
            x, y = px(t50, 0.5)
            ax.plot([X0, x], [y, y], color=color, alpha=0.55, lw=0.012 * pt, ls=(0, (3, 3.5)))
            ax.plot([x, x], [y, Y0], color=color, alpha=0.55, lw=0.012 * pt, ls=(0, (3, 3.5)))

    def rings(ax):
        for color, (xs, ss, lo, hi, m) in arms:
            x, y = px(xs[np.argmax(ss <= 0.5)], 0.5)
            ax.plot([x], [y], 'o', mfc=NAVY, mec=color, mew=0.016 * pt, ms=0.15 * pt)

    # glows first, then the bands, the curves, the guides
    gl = layer(ppi, lambda ax: curves(ax, lw=0.07, marks=False))
    for sigma, op in ((0.20 * inch, 0.55), (0.06 * inch, 0.45)):
        blur = np.stack([gaussian_filter(gl[..., i] * gl[..., 3], sigma) for i in range(3)] + [gaussian_filter(gl[..., 3], sigma)], -1)
        rgb = blur[..., :3] / np.maximum(blur[..., 3:4], 1e-6)
        img = screen(img, np.concatenate([rgb, blur[..., 3:4]], -1), op)
    del gl
    img = over(img, layer(ppi, bands))
    img = over(img, layer(ppi, axes_guides))
    if MEDIANS:
        img = over(img, layer(ppi, medians))
    img = over(img, layer(ppi, curves))
    if MEDIANS:
        img = over(img, layer(ppi, rings))

    # a dither of one level where the picture is not flat, so that the glows do not band and the file stays small
    flat = np.abs(img - NAVY.astype(np.float32)).max(-1) > 0
    noise = (rng.random((h, w, 1), dtype=np.float32) + rng.random((h, w, 1), dtype=np.float32) - 1) / 255
    img = img + noise * flat[..., None]
    out = np.clip(np.rint(img * 255), 0, 255).astype(np.uint8)
    from PIL import Image
    Image.fromarray(out).save(a.out, dpi=(ppi, ppi), optimize=True)
    print(f'{a.out}: {w} x {h} px at {ppi} ppi')


if __name__ == '__main__':
    main()
