import nose.tools as nt

from nbconvert.filters import get_metadata

def test_get_metadata():
    output = {
        'metadata': {
            'width': 1,
            'height': 2,
            'image/png': {
                'unconfined': True,
                'height': 3,
            }
        }
    }
    nt.assert_is(get_metadata(output, 'nowhere'), None)
    nt.assert_equal(get_metadata(output, 'height'), 2)
    nt.assert_equal(get_metadata(output, 'unconfined'), None)
    nt.assert_equal(get_metadata(output, 'unconfined', 'image/png'), True)
    nt.assert_equal(get_metadata(output, 'width', 'image/png'), 1)
    nt.assert_equal(get_metadata(output, 'height', 'image/png'), 3)
