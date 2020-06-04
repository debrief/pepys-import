import unittest

from pepys_import.file.highlighter.support.test_utils import create_test_line_object


def test_quoted_sensor_names():
    line = create_test_line_object(
        ";SENSOR2:	700103	034025.000	Frigate	@A	NULL	59 170 78 	5475	Frigate_Optic4 some message"
    )
    assert "Frigate_Optic4" in [token.text for token in line.tokens()]

    line_1 = create_test_line_object(
        ';SENSOR2:	700103	034125.000	Frigate	@A	NULL	55 170 78 	4777	"Frigate Optic5" some message'
    )
    assert "Frigate Optic5" in [token.text for token in line_1.tokens()]

    line_2 = create_test_line_object(
        ';SENSOR2:	700103	034425.000	Frigate	@A	NULL	33 205 76 	2934	" Frigate Optic5" some message'
    )
    assert "Frigate Optic5" in [token.text for token in line_2.tokens()]
    assert " Frigate Optic5" not in [token.text for token in line_2.tokens()]

    line_3 = create_test_line_object(
        ';SENSOR2:	700103	034525.000	Frigate	@A	NULL	21 220 76 	2458	"Frigate Optic5 " some message'
    )
    assert "Frigate Optic5" in [token.text for token in line_3.tokens()]
    assert "Frigate Optic5 " not in [token.text for token in line_3.tokens()]

    line_4 = create_test_line_object(
        ';SENSOR2:	700103	034625.000	Frigate	@A	NULL	7 230  76 	2089	" Frigate Optic5 " some message'
    )
    assert "Frigate Optic5" in [token.text for token in line_4.tokens()]
    assert " Frigate Optic5 " not in [token.text for token in line_4.tokens()]


if __name__ == "__main__":
    unittest.main()
