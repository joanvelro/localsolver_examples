#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""

    https://docs.scipy.org/doc/scipy/reference/tutorial/optimize.html#nelder-mead-simplex-algorithm-method-nelder-mead

    https://es.wikipedia.org/wiki/M%C3%A9todo_Nelder-Mead

    https://en.wikipedia.org/wiki/Test_functions_for_optimization


"""

import localsolver
import sys
import math
import numpy
import matplotlib
import matplotlib.pyplot

# matplotlib.pyplot.style.use('fivethirtyeight')# fivethirtyeight ggplot

import scipy.optimize


def cuadratic(x):
    """
        *Cuadratic function*



        :param x: list with input parameters
    """
    z = (x[1] ** 3 - 1) * numpy.cos(x[0])
    return z


def sphere(x):
    """
        *Sphere function*



        :param x: list with input parameters
    """
    z = x[0] ** 2 + x[1] ** 2
    return z


def hosaki(x):
    """
        *Hosaki function*

        0<=xi<=10; i=1,2
        fmin(x*) = -2.34
        x* = (4,2)

        :param x: list with input parameters
    """
    x1 = x[0]
    x2 = x[1]  # y
    z = ((1 - 8 * x1 + 7 * pow(x1, 2) - 7 * pow(x1, 3) / 3 + pow(x1, 4) / 4) * pow(x2, 2)
         * numpy.exp(-x2))
    return z


def hat_function(x):
    """
        *hat_function*


    """
    z = numpy.sin(numpy.sqrt(x[0] ** 2 + x[1] ** 2))
    return z


def rosembrock(x):
    """
        *Rosembrock Function*

        :param x: list with input parameters


    """
    a = 1
    b = 100
    z = (a - x[0]) ** 2 + b * (x[1] - x[0] ** 2) ** 2
    return z


def prepare_input_arguments(n, x1_min, x2_min, x1_max, x2_max):
    """
        *Prepare Input arguments*

    """
    # we create two 1D arrays of the desired lengths:
    x_1d = numpy.linspace(x1_min, x1_max, n)
    x_2d = numpy.linspace(x2_min, x2_max, n)

    # And we use the meshgrid function to create the X and Y matrices!
    X1, X2 = numpy.meshgrid(x_1d, x_2d)

    return X1, X2


def plot_surf(x, y, z, title, azim, elev):
    """
        *Plot function with two arguments*

        :param x:
        :param y:
        :param z:

    """
    fig = matplotlib.pyplot.figure(figsize=(8, 6))
    ax = fig.add_subplot(111,
                         projection='3d')

    surf = ax.plot_surface(x,
                           y,
                           z,
                           rstride=2,
                           cstride=2,
                           alpha=0.7,
                           cmap=matplotlib.cm.jet,  # coolwarm
                           linewidth=0,
                           antialiased=False)

    # ax.contour(x, y, z, zdir='z', offset=round(z[0, :].min() * 3), cmap=matplotlib.cm.jet)
    # ax.contour(x, y, z, zdir='y', offset=round(y[0, :].min() * 1.5), cmap=matplotlib.cm.jet)

    # ax.set_zlim(round(z[0, :].min() * 1.5), round(z[0, :].max() * 1.5))
    # ax.set_xlim(round(x[0, :].min() * 1.5), round(x[0, :].max() * 1.5))
    # ax.set_ylim(round(y[:, 0].min() * 1.5), round(y[:, 0].max() * 1.5))

    ax.set_xlabel('X1')
    ax.set_ylabel('X2')
    ax.set_zlabel('Z')
    # ax.set_title(title)

    ax.view_init(azim=azim,
                 elev=elev)

    fig.colorbar(surf, shrink=0.4, aspect=5)

    matplotlib.pyplot.show()
    matplotlib.pyplot.savefig(fname='{}.png'.format(title),
                              bbox_inches='tight',
                              pad_inches=0)
    matplotlib.pyplot.close()


def plot_contour(x, y, z, title, z_level_min, z_level_max, level_curve_start, level_curve_finish):
    """

    """

    matplotlib.pyplot.figure(figsize=(22, 8))
    z_levels = z_level_max * 10
    levels = numpy.linspace(z_level_min, z_level_max, z_levels)
    matplotlib.pyplot.contourf(x, y, z, levels, cmap=matplotlib.pyplot.cm.jet)
    matplotlib.pyplot.colorbar()
    matplotlib.pyplot.grid(b=True)

    # add level curves

    levels = numpy.linspace(level_curve_start, level_curve_finish, round(level_curve_finish*1.5))
    #print(levels)
    cs = matplotlib.pyplot.contour(x, y, z, levels, colors='k')
    matplotlib.pyplot.clabel(cs)
    matplotlib.pyplot.xlabel('X1')
    matplotlib.pyplot.ylabel('x2')
    matplotlib.pyplot.show()
    matplotlib.pyplot.savefig(fname='{}.png'.format(title),
                              bbox_inches='tight',
                              pad_inches=0)
    matplotlib.pyplot.close()


def plot_surf_with_result(x, y, z, xs, ys, zs, title, azim, elev):
    """
        *Plot function with two arguments*

        :param x:
        :param y:
        :param z:

    """
    fig = matplotlib.pyplot.figure(figsize=(8, 6))
    ax = fig.add_subplot(111,
                         projection='3d')

    surf = ax.plot_surface(x,
                           y,
                           z,
                           rstride=2,
                           cstride=2,
                           alpha=0.5,
                           cmap=matplotlib.cm.jet,  # coolwarm
                           linewidth=0,
                           antialiased=False)

    ax.scatter(xs,
               ys,
               zs,
               c='red',
               s=40)

    ax.set_xlabel('X1')
    ax.set_ylabel('X2')
    ax.set_zlabel('Z')
    # ax.set_title(title)

    ax.view_init(azim=azim,
                 elev=elev)

    fig.colorbar(surf, shrink=0.4, aspect=5)

    matplotlib.pyplot.show()
    matplotlib.pyplot.savefig(fname='{}.png'.format(title),
                              bbox_inches='tight',
                              pad_inches=0)
    matplotlib.pyplot.close()


def main_LS(evaluation_limit, output_file, function):
    """
        *Optimization with Local Solver Black Box Function*


    """
    with localsolver.LocalSolver() as ls:
        # Declares the optimization model
        model = ls.model

        # Numerical decisions
        x1 = model.float(0, 5)
        x2 = model.float(0, 6)

        # Creates and calls blackbox function
        f = model.create_double_blackbox_function(function)
        bb_call = model.call(f, x1, x2)

        # Minimizes function call
        model.minimize(bb_call)
        model.close()

        # Parameterizes the solver
        f.blackbox_context.evaluation_limit = evaluation_limit

        ls.solve()

        # Writes the solution in a file
        if output_file is not None:
            with open(output_file, 'w') as f:
                f.write("obj=%f\n" % bb_call.value)
                f.write("x1=%f\n" % x1.value)
                f.write("x2=%f\n" % x2.value)

        solution = {'fs': bb_call.value,
                    'x1s': x1.value,
                    'x2s': x2.value}

        return solution


if __name__ == '__main__':

    f_rosembrock = False
    f_hosaky = False
    f_hat_function = False
    f_sphere = True
    f_cuadratic = False

    if f_cuadratic:
        X1, X2 = prepare_input_arguments(n=200,
                                         x1_min=-8,
                                         x2_min=-8,
                                         x1_max=8,
                                         x2_max=8)
        Z = cuadratic([X1, X2])

        plot_surf(x=X1,
                  y=X2,
                  z=Z,
                  title='plot_cuadratic_surf',
                  azim=120,
                  elev=40)

        plot_contour(x=X1,
                     y=X2,
                     z=Z,
                     title='plot_cuadratic_contour',
                     z_level_min=-10,
                     z_level_max=10,
                     level_curve_start=-2,
                     level_curve_finish=2
        )

        print(':: Local Solver Solution ::')
        solution_LS = main_LS(evaluation_limit=30,
                              output_file='results_cuadratic',
                              function=cuadratic)

        print(':: Scipy Solution ::')
        x0 = numpy.array([1, 1])
        solution_SP = scipy.optimize.minimize(cuadratic,
                                              x0,
                                              method='Powell',
                                              options={'xtol': 1e-4,
                                                       'disp': True})

        plot_surf_with_result(x=X1,
                              y=X2,
                              z=Z,
                              xs=solution_LS['x1s'],
                              ys=solution_LS['x2s'],
                              zs=solution_LS['fs'],
                              title='plot_cuadratic_with_results',
                              azim=150,
                              elev=40,
                              )

    if f_sphere:
        X1, X2 = prepare_input_arguments(n=200,
                                         x1_min=-10,
                                         x2_min=-10,
                                         x1_max=10,
                                         x2_max=10)
        Z = sphere([X1, X2])

        plot_surf(x=X1,
                  y=X2,
                  z=Z,
                  title='plot_sphere_surf',
                  azim=150,
                  elev=40)

        plot_contour(x=X1,
                     y=X2,
                     z=Z,
                     title='plot_sphere_contour',
                     z_level_min=0,
                     z_level_max=150,
                     level_curve_start=-50,
                     level_curve_finish=50
                     )

        print(':: Local Solver Solution ::')
        solution_LS = main_LS(evaluation_limit=30,
                              output_file='results_sphere',
                              function=sphere)

        print(':: Scipy Solution ::')
        x0 = numpy.array([1, 1])
        solution_SP = scipy.optimize.minimize(sphere,
                                              x0,
                                              method='Powell',
                                              options={'xtol': 1e-4,
                                                       'disp': True})

        plot_surf_with_result(x=X1,
                              y=X2,
                              z=Z,
                              xs=solution_LS['x1s'],
                              ys=solution_LS['x2s'],
                              zs=solution_LS['fs'],
                              title='sphere',
                              azim=150,
                              elev=40,
                              )

    if f_hat_function:
        X1, X2 = prepare_input_arguments(n=200,
                                         x1_min=-10,
                                         x2_min=-10,
                                         x1_max=10,
                                         x2_max=10)
        Z = hat_function([X1, X2])

        plot_surf(x=X1,
                  y=X2,
                  z=Z,
                  title='plot_hat_function_surf',
                  azim=150,
                  elev=40)

        plot_contour(x=X1,
                     y=X2,
                     z=Z,
                     title='plot_hat_function_contour',
                     z_level_min=-1,
                     z_level_max=1,
                     level_curve_start=-0.5,
                     level_curve_finish=0.5
                     )

        print(':: Local Solver Solution ::')
        solution_LS = main_LS(evaluation_limit=30,
                              output_file='results_hat_function',
                              function=hat_function)

        print(':: Scipy Solution ::')
        x0 = numpy.array([1, 1])
        solution_SP = scipy.optimize.minimize(hat_function,
                                              x0,
                                              method='Powell',
                                              options={'xtol': 1e-4,
                                                       'disp': True})

        plot_surf_with_result(x=X1,
                              y=X2,
                              z=Z,
                              xs=solution_LS['x1s'],
                              ys=solution_LS['x2s'],
                              zs=solution_LS['fs'],
                              title='hat_function',
                              azim=150,
                              elev=40,
                              )

    if f_rosembrock:
        X1, X2 = prepare_input_arguments(n=200,
                                         x1_min=-1,
                                         x2_min=-1,
                                         x1_max=1,
                                         x2_max=1)
        Z = rosembrock([X1, X2])

        plot_surf(x=X1,
                  y=X2,
                  z=Z,
                  title='plot_rosembrock_surf',
                  azim=150,
                  elev=40)

        plot_contour(x=X1,
                     y=X2,
                     z=Z,
                     title='plot_rosembrock_contour')

        print(':: Local Solver Solution ::')
        solution_LS = main_LS(evaluation_limit=30,
                              output_file='results',
                              function=rosembrock)

        print(':: Scipy Solution ::')
        x0 = numpy.array([1, 1])
        solution_SP = scipy.optimize.minimize(rosembrock,
                                              x0,
                                              method='Powell',
                                              options={'xtol': 1e-4,
                                                       'disp': True})

        plot_surf_with_result(x=X1,
                              y=X2,
                              z=Z,
                              xs=solution_LS['x1s'],
                              ys=solution_LS['x2s'],
                              zs=solution_LS['fs'],
                              title='plot_rosembrock_surf_with_results',
                              azim=150,
                              elev=40,
                              )

    if f_hosaky:
        X1, X2 = prepare_input_arguments(n=200,
                                         x1_min=-1,
                                         x2_min=-1,
                                         x1_max=1,
                                         x2_max=1)
        Z = hosaki([X1, X2])

        plot_surf(x=X1,
                  y=X2,
                  z=Z,
                  title='hosaky',
                  azim=150,
                  elev=40)

        plot_contour(x=X1,
                     y=X2,
                     z=Z,
                     title='hosaky')

        print(':: Local Solver Solution ::')
        solution_LS = main_LS(evaluation_limit=30,
                              output_file='results',
                              function=hosaki)

        print(':: Scipy Solution ::')
        x0 = numpy.array([4, 2])
        solution_SP = scipy.optimize.minimize(fun=hosaki,
                                              x0=x0,
                                              method='Powell',  # Newton-CG Powell nelder-mead
                                              options={'xtol': 1e-4,
                                                       'disp': True})

        plot_surf_with_result(x=X1,
                              y=X2,
                              z=Z,
                              xs=solution_LS['x1s'],
                              ys=solution_LS['x2s'],
                              zs=solution_LS['fs'],
                              title='hosaky',
                              azim=150,
                              elev=40)
