import unittest
from pybis2spice import pybis2spice
import numpy as np
import ecdtools
from ecdtools.ibis import TypMinMax


class TestPybis2Spice(unittest.TestCase):

    def test_extract_range_param(self):
        # Test an empty TypMinMax object
        data = TypMinMax()
        data.typical = None
        data.minimum = None
        data.maximum = None
        self.assertEqual(pybis2spice.extract_range_param(data), None)

        data.typical = 1e-9
        data.minimum = 8.341E-02
        np.testing.assert_equal(pybis2spice.extract_range_param(data), [1e-9, 8.341E-02, None])

        data.typical = None
        data.minimum = None
        data.maximum = 3e-12
        np.testing.assert_equal(pybis2spice.extract_range_param(data), [None, None, 3e-12])

        # Test values from some test Ibis files
        ibis_file = 'ibis/bird57ex.ibs'
        ibis = ecdtools.ibis.load_file(ibis_file, transform=True)
        component = ibis.get_component_by_name('BIRD57ex')
        np.testing.assert_equal(pybis2spice.extract_range_param(component.package.r_pkg), [0.1, None, None])
        np.testing.assert_equal(pybis2spice.extract_range_param(component.package.l_pkg), [8e-9, None, None])
        np.testing.assert_equal(pybis2spice.extract_range_param(component.package.c_pkg), [5e-12, None, None])

        ibis_file = 'ibis/hct1g08.ibs'
        ibis = ecdtools.ibis.load_file(ibis_file, transform=True)
        component = ibis.get_component_by_name('74HCT1G08_GW')
        model = ibis.get_model_by_name('HCT1G08_IN_50')
        self.assertEqual(pybis2spice.extract_range_param(model.pullup_reference), None)
        np.testing.assert_equal(pybis2spice.extract_range_param(model.c_comp), [2.8774e-12, 1.2578e-12, 5.2328e-12])
        np.testing.assert_equal(pybis2spice.extract_range_param(component.package.r_pkg),
                                [8.353E-02, 8.341E-02, 8.366E-02])

    def test_extract_iv_table(self):
        ibis_file = 'ibis/bushold.ibs'
        ibis = ecdtools.ibis.load_file(ibis_file, transform=True)
        model = ibis.get_model_by_name('TOP_MODEL_BUS_HOLD')

        from decimal import Decimal
        test = [(Decimal('2'), Decimal('0'), Decimal('0'), Decimal('0')),
                (Decimal('1'), Decimal('0'), Decimal('0'), Decimal('0'))]
        # Test the inversion
        np.testing.assert_equal(pybis2spice.extract_iv_table(test),
                                [[1, 0, 0, 0],
                                 [2, 0, 0, 0]])

        np.testing.assert_equal(pybis2spice.extract_iv_table(model.pullup),
                                [[-5.0e+00,  1.0e-04,  8.0e-05,  1.2e-04],
                                [-1.0e+00,  3.0e-05,  2.5e-05,  4.0e-05],
                                [0.0e+00,  0.0e+00,  0.0e+00,  0.0e+00],
                                [1.0e+00, -3.0e-05, -2.5e-05, -4.0e-05],
                                [3.0e+00, -5.0e-05, -4.5e-05, -5.0e-05],
                                [5.0e+00, -1.0e-04, -8.0e-05, -1.2e-04],
                                [1.0e+01, -1.2e-04, -9.0e-05, -1.5e-04]])

        np.testing.assert_equal(pybis2spice.extract_iv_table(model.gnd_clamp),
                                [[-2.0, -6.158e+17, np.nan, np.nan],
                                [-1.9, -1.697e+16, np.nan, np.nan],
                                [-1.8, -467900000000000.0, np.nan, np.nan],
                                [-1.7, -12900000000000.0, np.nan, np.nan],
                                [-1.6, -355600000000.0, np.nan, np.nan],
                                [-1.5, -9802000000.0, np.nan, np.nan],
                                [-1.4, -270200000.0, np.nan, np.nan],
                                [-1.3, -7449000.0, np.nan, np.nan],
                                [-1.2, -205300.0, np.nan, np.nan],
                                [-1.1, -5660.0, np.nan, np.nan],
                                [-1.0, -156.0, np.nan, np.nan],
                                [-0.9, -4.308, np.nan, np.nan],
                                [-0.8, -0.1221, np.nan, np.nan],
                                [-0.7, -0.004315, np.nan, np.nan],
                                [-0.6, -0.0001715, np.nan, np.nan],
                                [-0.5, -4.959e-06, np.nan, np.nan],
                                [-0.4, -1.373e-07, np.nan, np.nan],
                                [-0.3, -4.075e-09, np.nan, np.nan],
                                [-0.2, -3.044e-10, np.nan, np.nan],
                                [-0.1, -1.03e-10, np.nan, np.nan],
                                [0.0, 0.0, np.nan, np.nan],
                                [5.0, 0.0, np.nan, np.nan]])

        np.testing.assert_equal(pybis2spice.extract_iv_table(model.gnd_clamp),
                                [[-2.0, -6.158e+17, np.nan, np.nan],
                                 [-1.9, -1.697e+16, np.nan, np.nan],
                                 [-1.8, -467900000000000.0, np.nan, np.nan],
                                 [-1.7, -12900000000000.0, np.nan, np.nan],
                                 [-1.6, -355600000000.0, np.nan, np.nan],
                                 [-1.5, -9802000000.0, np.nan, np.nan],
                                 [-1.4, -270200000.0, np.nan, np.nan],
                                 [-1.3, -7449000.0, np.nan, np.nan],
                                 [-1.2, -205300.0, np.nan, np.nan],
                                 [-1.1, -5660.0, np.nan, np.nan],
                                 [-1.0, -156.0, np.nan, np.nan],
                                 [-0.9, -4.308, np.nan, np.nan],
                                 [-0.8, -0.1221, np.nan, np.nan],
                                 [-0.7, -0.004315, np.nan, np.nan],
                                 [-0.6, -0.0001715, np.nan, np.nan],
                                 [-0.5, -4.959e-06, np.nan, np.nan],
                                 [-0.4, -1.373e-07, np.nan, np.nan],
                                 [-0.3, -4.075e-09, np.nan, np.nan],
                                 [-0.2, -3.044e-10, np.nan, np.nan],
                                 [-0.1, -1.03e-10, np.nan, np.nan],
                                 [0.0, 0.0, np.nan, np.nan],
                                 [5.0, 0.0, np.nan, np.nan]])

    def test_adjust_device_data(self):
        device = np.asarray([[0, 10, 10, 10], [1, 10, 10, 10], [2, 10, 10, 10]])
        clamp = np.asarray([[0, 0, 0, 0], [1, 0, 0, 0], [2, 0, 0, 0]])
        clamp_pos = np.asarray([[0, 1, 1, 1], [1, 1, 1, 1], [2, 1, 1, 1]])
        clamp_neg = np.asarray([[0, -1, -1, -1], [1, -1, -1, -1], [2, -1, -1, -1]])
        result1 = pybis2spice.adjust_device_data(device, clamp)
        result2 = pybis2spice.adjust_device_data(device, clamp_pos)
        result3 = pybis2spice.adjust_device_data(device, clamp_neg)

        device2 = np.asarray([[0, 10, 10, 10], [-1, 10, 10, 10], [-2, 10, 10, 10]])
        clamp2 = np.asarray([[0, 0, 0, 0], [-1, 0, 0, 0], [-2, 0, 0, 0]])
        clamp2_pos = np.asarray([[0, 1, 1, 1], [-1, 1, 1, 1], [-2, 1, 1, 1]])
        clamp2_neg = np.asarray([[0, -1, -1, -1], [-1, -1, -1, -1], [-2, -1, -1, -1]])
        result4 = pybis2spice.adjust_device_data(device2, clamp2)
        result5 = pybis2spice.adjust_device_data(device2, clamp2_pos)
        result6 = pybis2spice.adjust_device_data(device2, clamp2_neg)

        # interpolate
        device3 = np.asarray([[0, 0, 0, 0], [1, 1, 1, 1], [2, 2, 2, 2]])
        clamp3 = np.asarray([[0, 0, 0, 0], [1.5, 1.5, 1.5, 1.5], [2, 2, 2, 2]])
        result7 = pybis2spice.adjust_device_data(device3, clamp3)

        np.testing.assert_equal(result1, np.asarray([[0, 10, 10, 10], [1, 10, 10, 10], [2, 10, 10, 10]]))
        np.testing.assert_equal(result2, np.asarray([[0, 9, 9, 9], [1, 9, 9, 9], [2, 9, 9, 9]]))
        np.testing.assert_equal(result3, np.asarray([[0, 11, 11, 11], [1, 11, 11, 11], [2, 11, 11, 11]]))
        np.testing.assert_equal(result4, np.asarray([[0, 10, 10, 10], [-1, 10, 10, 10], [-2, 10, 10, 10]]))
        np.testing.assert_equal(result5, np.asarray([[0, 9, 9, 9], [-1, 9, 9, 9], [-2, 9, 9, 9]]))
        np.testing.assert_equal(result6, np.asarray([[0, 11, 11, 11], [-1, 11, 11, 11], [-2, 11, 11, 11]]))
        np.testing.assert_equal(result7, np.asarray([[0, 0, 0, 0], [1, 0, 0, 0], [2, 0, 0, 0]]))

    def test_increasing(self):
        self.assertEqual(pybis2spice.increasing([0, 0, 0, 0]), True)
        self.assertEqual(pybis2spice.increasing([0, 1, 0, 0]), False)
        self.assertEqual(pybis2spice.increasing([0, 1, 2, 3]), True)
        self.assertEqual(pybis2spice.increasing([0, 1, 1, 39000]), True)

    def test_get_current_data_from_iv_data(self):
        # TODO test_get_current_data_from_iv_data
        pass

    def test_get_reference(self):
        v_range = np.asarray([4.5, 5, 5.5])
        ref1 = np.asarray([3, 3.3, 3.6])
        ref2 = None

        # Test when the ref parameter is not None. The output should be equal to the v_range
        self.assertEqual(pybis2spice.get_reference(ref1, v_range, 1), 3)
        self.assertEqual(pybis2spice.get_reference(ref1, v_range, 2), 3.3)
        self.assertEqual(pybis2spice.get_reference(ref1, v_range, 3), 3.6)

        # Test when the ref parameter is None. The output should be equal to the v_range
        self.assertEqual(pybis2spice.get_reference(ref2, v_range, 1), 4.5)
        self.assertEqual(pybis2spice.get_reference(ref2, v_range, 2), 5)
        self.assertEqual(pybis2spice.get_reference(ref2, v_range, 3), 5.5)

        # Testing when v_range parameter is 0, so the output should be 0
        self.assertEqual(pybis2spice.get_reference(ref2, 0, 1), 0)
        self.assertEqual(pybis2spice.get_reference(ref2, 0, 2), 0)
        self.assertEqual(pybis2spice.get_reference(ref2, 0, 3), 0)

    def test_generating_current_data(self):
        # TODO test_generating_current_data
        pass

    def test_solve_k_params_output(self):
        # TODO test_solve_k_params_output
        pass

    def test_differentiate(self):
        np.testing.assert_equal(pybis2spice.differentiate([0, 1, 2, 3], [0, 1, 2, 3]), [1, 1, 1, 1])
        np.testing.assert_equal(pybis2spice.differentiate([1, 1, 1, 1], [0, 1, 2, 3]), [0, 0, 0, 0])
        np.testing.assert_equal(pybis2spice.differentiate([10, 10, 200, 20], [0, 1, 2, 3]), [0, 190, -180, -180])

    def test_compress_param(self):
        k_param = np.asarray([[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 1, 1], [4, 2, 2], [5, 2, 2], [6, 2, 2]])
        k_compressed = np.asarray([[2, 0, 0], [3, 1, 1]])

        np.testing.assert_equal(pybis2spice.compress_param(k_param), k_compressed)

        #np.testing.assert_equal(pybis2spice.compress_param([4, 4, 3, 2, 1, 0, 0]), [4, 3, 2, 1, 0])
        #np.testing.assert_equal(pybis2spice.compress_param([4, 4, 3, 2, 1, 0, 0], threshold=1.5), [4, 4, 3, 2, 1, 0, 0])
        #np.testing.assert_equal(pybis2spice.compress_param([4.6, 4, 3, 2, 1, 0.6, 0.2], threshold=0.5), [4, 3, 2, 1, 0.6, 0.2])


    #  TODO Test the functions for the subcircuit creation. Probably better to check the files


if __name__ == '__main__':
    unittest.main()
