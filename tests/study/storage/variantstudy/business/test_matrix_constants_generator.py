import numpy as np
from antarest.matrixstore.service import SimpleMatrixService
from antarest.study.storage.variantstudy.business import matrix_constants
from antarest.study.storage.variantstudy.business.matrix_constants_generator import (
    MATRIX_PROTOCOL_PREFIX,
    GeneratorMatrixConstants,
)


class TestGeneratorMatrixConstants:
    def test_get_st_storage(self, tmp_path):
        generator = GeneratorMatrixConstants(
            matrix_service=SimpleMatrixService(bucket_dir=tmp_path)
        )

        ref1 = generator.get_st_storage_pmax_injection()
        matrix_id1 = ref1.split(MATRIX_PROTOCOL_PREFIX)[1]
        matrix_dto1 = generator.matrix_service.get(matrix_id1)
        assert (
            np.array(matrix_dto1.data).all()
            == matrix_constants.st_storage.series.pmax_injection.all()
        )

        ref2 = generator.get_st_storage_pmax_withdrawal()
        matrix_id2 = ref2.split(MATRIX_PROTOCOL_PREFIX)[1]
        matrix_dto2 = generator.matrix_service.get(matrix_id2)
        assert (
            np.array(matrix_dto2.data).all()
            == matrix_constants.st_storage.series.pmax_withdrawal.all()
        )

        ref3 = generator.get_st_storage_lower_rule_curve()
        matrix_id3 = ref3.split(MATRIX_PROTOCOL_PREFIX)[1]
        matrix_dto3 = generator.matrix_service.get(matrix_id3)
        assert (
            np.array(matrix_dto3.data).all()
            == matrix_constants.st_storage.series.lower_rule_curve.all()
        )

        ref4 = generator.get_st_storage_upper_rule_curve()
        matrix_id4 = ref4.split(MATRIX_PROTOCOL_PREFIX)[1]
        matrix_dto4 = generator.matrix_service.get(matrix_id4)
        assert (
            np.array(matrix_dto4.data).all()
            == matrix_constants.st_storage.series.upper_rule_curve.all()
        )

        ref5 = generator.get_st_storage_inflows()
        matrix_id5 = ref5.split(MATRIX_PROTOCOL_PREFIX)[1]
        matrix_dto5 = generator.matrix_service.get(matrix_id5)
        assert (
            np.array(matrix_dto5.data).all()
            == matrix_constants.st_storage.series.inflows.all()
        )
