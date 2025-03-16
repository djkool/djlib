from xml.dom.minidom import Attr
import pytest
from primitives import Vector, Size

def approx(dec_points=3):
    """check 2 floating point numbers are aproximatly equal
    dec_points specifies the number of decimal points to check to
    returns a function that can be used to compare 2 (floating point)
    values
    
    function returned can also take an optional 'reason' that is passed
    to the assert statment
    """
    # Check that numbers are close to the expected value
    # as diffrent python versions/implementations return
    # diffrent values for floating point numbers
    def compare(a, b, reason=None):
        val = abs(b - a)
        assert val < (10 ** -dec_points), reason
    return compare
approx = approx()

@pytest.fixture
def coords():
    return (1,2,3)

@pytest.fixture
def vector(coords):
    """Dependency injection of a standardised vector"""
    return Vector(*coords)

@pytest.fixture
def size():
    """Dependency injection of a standardised size"""
    return Size(1,2,3)

## Vector ##
class TestVector:

    def test_repr(self, vector):
        """Check that the repr string creation code works, 
        commonly overlooked"""
        r = repr(vector)
        assert r == "<1, 2, 3>"

    def test_addition(self, vector):
        v = vector + vector
        assert v == Vector(2,4,6)

    def test_inplace_addition(self, vector):
        vector += vector
        assert vector == Vector(2,4,6)

    def test_subtraction(self, vector):
        v = vector - vector
        assert v == Vector(0,0,0)

    def test_inplace_subtraction(self, vector):
        vector -= vector
        assert vector == Vector(0,0,0)

    @pytest.mark.parametrize("vect_or_scale, expected",
                             [( Vector(1,2,3), 14),
                              ( 5, Vector(5,10,15))]
                            )
    def test_multiplication(self, vector, vect_or_scale, expected):
        v = vector * vect_or_scale
        assert v == expected

    def test_inplace_multiplication(self, vector):
        vector *= 5
        assert vector == Vector(5,10,15)

    def test_negate(self, vector):
        v = -vector
        assert v == Vector(-1,-2,-3)

    def test_equal(self, vector, coords):
        for i, val in enumerate(coords):
            assert vector[i] == val

        v = Vector(*coords)
        assert vector == v

    def test_attributes(self, vector):
        # we are only testing the implementation, not that the 
        # returned values are correct here as unlike the other
        # operations there should be no calculations, only
        # storage
        assert vector.x == vector.x
        assert vector.y == vector.y
        assert vector.z == vector.z

        with pytest.raises(AttributeError):
            vector.q

        v = Vector(0,0,0)
        v.x = vector.x
        v.y = vector.y
        v.z = vector.z
        assert v == vector

    def test_set(self, vector, coords):
        v = Vector(0,0,0)
        v.set(coords[0], coords[1], coords[2])
        assert v == vector

        v.set(*coords)
        assert v == vector

    def test_length(self, vector):
        l = vector.length()
        approx(l, 3.742)

    def test_scaled(self, vector):
        v = vector * 5
        assert v == Vector(5,10,15)

    def test_normalized(self, vector):
        vector = vector.normalized()
        v = Vector(0.267, 0.534, 0.801)
        approx(vector.x, v.x)
        approx(vector.y, v.y)
        approx(vector.z, v.z)

        approx(vector.length(), 1.0)

    def test_clear(self, vector):
        vector.clear()
        assert vector == Vector(0,0,0)

    def test_distanceApart(self, vector):
        approx(vector.distanceApart(vector), 0.0)

    @pytest.mark.parametrize("d", [0.0, 0.5, 1.0])
    def test_interpolate(self, vector, d):
        v = Vector(0,0,0)
        approx(v.interpolate(vector, d).length(), vector.length() * d)

# end TestVector

## Size ##
class TestSize:
    def test_repr(self, size):
        """Check that the repr string creation code works, 
        commonly overlooked"""
        r = repr(size)

    def test_attributes(self, size):
        # we are only testing the implementation, not that the 
        # returned values are correct here as unlike the other
        # operations there should be no calculations, only
        # storage
        assert size.w == size.w
        assert size.h == size.h
        assert size.l == size.l

        with pytest.raises(AttributeError):
            size.q

        s = Size(0,0,0)
        s.w = size.w
        s.h = size.h
        s.l = size.l
        assert s == size


#def test_bounding_volumes():
#    print "BOUND VOLUMES TEST".center(30, "=")

