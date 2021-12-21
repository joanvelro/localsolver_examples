#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
    Blending



"""
import localsolver
import sys
import pandas


def main(time_limit, file_name):
    with localsolver.LocalSolver() as ls:

        #
        # Declares the optimization model
        #
        model = ls.model

        # ::: Parametros :::

        # Demanda producto final
        QD = 30000

        # Previo venta
        p_venta = 500

        # Limites specs
        limit_azufre = 0.5
        limit_densidad = 0.95

        # Cantidades min./max. compra
        Qmin = 500
        Qmax = 10000

        # Nivel stock producto



        stock = [1450, 1350, 1260]

        # costes adquisicion componentes y stock
        Pc = [470, 400, 460]
        Pk = [450, 430, 400]

        # Propiedades

        densidad_c = [0.93, 0.92, 0.87]
        densidad_s = [0.89, 0.9, 0.98]

        azufre_c = [0.57, 0.47, 0.45]
        azufre_s = [0.52, 0.51, 0.51]

        # ::: Variables :::

        # Variables cantidad componentes y stock a usar
        n_tanks = 3
        n_components = 3
        Qc = [model.int(Qmin, Qmax) for i in range(n_components)]
        Qs = [model.int(Qmin, Qmax) for i in range(n_tanks)]

        # binary variables for quantities
        yc = [model.int(0, 1) for i in range(n_components)]
        ys = [model.int(0, 1) for i in range(n_tanks)]

        stock_used = model.sum(Qs[i] for i in range(n_tanks))
        stock_total = model.sum(stock[i] for i in range(n_tanks))

        # ====================
        # ::: Constraints :::
        # ====================

        # Total stock to use
        model.constraint(stock_used <= stock_total)

        # Demand constraint
        total_production = model.sum(Qc[i] * yc[i] for i in range(n_components)) + \
                           model.sum(Qs[i] * ys[i] for i in range(n_tanks))

        model.constraint(total_production >= QD)

        # Restriccion densidad
        final_density = (1 / total_production) * (model.sum(densidad_c[i] * Qc[i] * yc[i] for i in range(n_components)) +
                                                  model.sum(densidad_s[i] * Qs[i] * ys[i] for i in range(n_tanks)))

        model.constraint(final_density <= limit_densidad)

        # Restriccion azufre
        final_azufre = (1 / total_production) * (model.sum(azufre_c[i] * Qc[i] * yc[i] for i in range(n_components)) +
                                                 model.sum(azufre_s[i] * Qs[i] * ys[i] for i in range(n_tanks)))
        model.constraint(final_azufre <= limit_azufre)

        # ::: Optimal function :::
        total_cost = model.sum(Qc[i] * yc[i] * Pc[i] for i in range(n_components)) + \
                     model.sum(Qs[i] * ys[i] * Pk[i] for i in range(n_tanks))

        model.minimize(total_cost)

        beneficios = total_production * p_venta - total_cost

        model.close()

        # ::: model params :::

        ls.param.time_limit = time_limit

        # ::: Solve model :::
        ls.solve()

        yc_ = [yc[i].value for i in range(n_components)]
        ys_ = [ys[i].value for i in range(n_tanks)]
        qc_ = [Qc[i].value for i in range(n_components)]
        qs_ = [Qs[i].value for i in range(n_tanks)]

        df_comp = pandas.DataFrame({'yc': yc_,
                                    'Qc': qc_})

        df_stock = pandas.DataFrame({'ys': ys_,
                                     'Qs': qs_})

        df_res = pandas.DataFrame({'total_cost': [total_cost.value],
                                   'beneficios': beneficios.value,
                                   'stock_used': stock_used.value,
                                   'total_production': total_production.value,
                                   'density': final_density.value,
                                   'azufre': final_azufre.value
                                   }
                                  )

        with open(file_name, 'w') as f:
            for i in range(n_tanks):
                f.write("Qs(%d):%f\n" % (i, Qs[i].value))
            for i in range(n_components):
                f.write("Qc(%d):%f\n" % (i, Qc[i].value))
            f.write("total_cost: %d M$\nstock_used:%f Tm\ntotal_production:%f Tm\ndensity:%f\nbeneficios:%f $/Tm\n" % (
                total_cost.value / 1000000, stock_used.value, total_production.value, final_density.value, beneficios.value / total_production.value))
            f.write("azufre:%f " % (
                final_azufre.value))

    return df_comp, df_stock, df_res


if __name__ == '__main__':


    df_comp, df_stock, df_res = main(time_limit=2,
                                     file_name='results_blending.txt')

    df_res['B'] = df_res['beneficios'] / df_res['total_production']
    df_res['CT'] = df_res['total_cost'] / 1000000
