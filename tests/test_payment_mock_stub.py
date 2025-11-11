import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from unittest.mock import Mock
from services.payment_service import PaymentGateway
from services.library_service import pay_late_fees, refund_late_fee_payment

def test_pay_late_fees_success(mocker):
    mocker.patch("services.library_service.calculate_late_fee_for_book", return_value={"fee_amount": 10})
    mocker.patch("services.library_service.get_book_by_id", return_value={"title": "Harry Potter"})
    
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.return_value = (True, "txn_123", "Success")

    success, result, output = pay_late_fees("482930", 1, mock_gateway)

    assert success is True
    assert "successful" in result.lower()
    assert output == "txn_123"
    mock_gateway.process_payment.assert_called_once_with(
        patron_id="482930",
        amount=10,
        description="Late fees for 'Harry Potter'"
    )


def test_pay_late_fees_decline(mocker):
    mocker.patch("services.library_service.calculate_late_fee_for_book", return_value={"fee_amount": 8})
    mocker.patch("services.library_service.get_book_by_id", return_value={"title": "Harry Potter"})

    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.return_value = (False, "", "Declined")

    success, result, output = pay_late_fees("482930", 1, mock_gateway)

    assert success is False
    assert "declined" in result.lower()
    assert output is None
    mock_gateway.process_payment.assert_called_once()


def test_pay_late_fees_invalid_patron_id(mocker):
    mocker.patch("services.library_service.calculate_late_fee_for_book")  
    mocker.patch("services.library_service.get_book_by_id")  
    mock_gateway = Mock(spec=PaymentGateway)

    success, result, output = pay_late_fees("67", 1, mock_gateway)

    assert success is False
    assert "invalid patron id" in result.lower()
    assert output is None
    mock_gateway.process_payment.assert_not_called()


def test_pay_late_fees_no_fee(mocker):
    mocker.patch("services.library_service.calculate_late_fee_for_book", return_value={"fee_amount": 0})
    mocker.patch("services.library_service.get_book_by_id", return_value={"title": "Harry Potter"})

    mock_gateway = Mock(spec=PaymentGateway)
    success, result, output = pay_late_fees("482930", 1, mock_gateway)

    assert success is False
    assert "no late fees" in result.lower()
    assert output is None
    mock_gateway.process_payment.assert_not_called()


def test_pay_late_fees_gateway_exception(mocker):
    mocker.patch("services.library_service.calculate_late_fee_for_book", return_value={"fee_amount": 5})
    mocker.patch("services.library_service.get_book_by_id", return_value={"title": "Harry Potter"})

    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.process_payment.side_effect = Exception("Network Failure")

    success, result, output = pay_late_fees("482930", 1, mock_gateway)

    assert success is False
    assert "error" in result.lower()
    assert output is None
    mock_gateway.process_payment.assert_called_once()


def test_pay_late_fees_book_not_found(mocker):
    mocker.patch("services.library_service.calculate_late_fee_for_book", return_value={"fee_amount": 5})
    mocker.patch("services.library_service.get_book_by_id", return_value=None)

    mock_gateway = Mock(spec=PaymentGateway)

    success, result, output = pay_late_fees("482930", 1, mock_gateway)

    assert success is False
    assert "book not found" in result.lower()
    assert output is None
    mock_gateway.process_payment.assert_not_called()


def test_refund_success():
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.return_value = (True, "refund success")

    success, result = refund_late_fee_payment("txn_123", 5, mock_gateway)

    assert success is True
    assert "refund success" in result.lower()
    mock_gateway.refund_payment.assert_called_once_with("txn_123", 5)


def test_refund_invalid_amount_above_max_limit():
    mock_gateway = Mock(spec=PaymentGateway)

    success, result = refund_late_fee_payment("txn_123", 25, mock_gateway)

    assert success is False
    mock_gateway.refund_payment.assert_not_called()


def test_refund_invalid_test_id():
    mock_gateway = Mock(spec=PaymentGateway)

    success, result = refund_late_fee_payment("invalid_id", 5, mock_gateway)

    assert success is False
    assert "invalid" in result.lower()
    mock_gateway.refund_payment.assert_not_called()


def test_refund_invalid_amount_negative():
    mock_gateway = Mock(spec=PaymentGateway)

    success, result = refund_late_fee_payment("txn_123", -5, mock_gateway)

    assert success is False
    mock_gateway.refund_payment.assert_not_called()


def test_refund_invalid_amount_zero():
    mock_gateway = Mock(spec=PaymentGateway)

    success, result = refund_late_fee_payment("txn_123", 0, mock_gateway)

    assert success is False
    mock_gateway.refund_payment.assert_not_called()


def test_refund_invalid_transaction():
    mock_gateway = Mock(spec=PaymentGateway)

    success, result = refund_late_fee_payment("abc123", 5, mock_gateway)

    assert success is False
    assert "invalid" in result.lower()
    mock_gateway.refund_payment.assert_not_called()


def test_refund_gateway_exception():
    mock_gateway = Mock(spec=PaymentGateway)
    mock_gateway.refund_payment.side_effect = Exception("Gateway Down")

    success, result = refund_late_fee_payment("txn_123", 5, mock_gateway)

    assert success is False
    assert "error" in result.lower()
    mock_gateway.refund_payment.assert_called_once()