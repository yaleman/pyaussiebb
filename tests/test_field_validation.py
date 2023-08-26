""" pyaussiebb tests """
import pytest

from aussiebb.baseclass import BaseClass
from aussiebb.exceptions import UnrecognisedServiceType


def test_validate_service_type() -> None:
    """testing the validate_service_type function"""

    test = BaseClass(
        username="foo",
        password="bar",
        debug=True,
    )

    assert test.validate_service_type({"type": "NBN", "name": "testservice"}) is None
    assert (
        test.validate_service_type({"type": "Hardware", "name": "testservice"}) is None
    )
    with pytest.raises(UnrecognisedServiceType):
        test.validate_service_type({"type": "Cheese", "name": "testservice"})
