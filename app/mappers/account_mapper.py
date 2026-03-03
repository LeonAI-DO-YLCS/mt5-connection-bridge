from ..models.account import AccountInfo


def map_mt5_account(acc) -> AccountInfo:
    """
    Map an MT5 account_info namedtuple to the AccountInfo Pydantic model.
    """
    return AccountInfo(
        login=acc.login,
        server=acc.server,
        balance=float(acc.balance),
        equity=float(acc.equity),
        margin=float(acc.margin),
        free_margin=float(acc.margin_free),
        profit=float(acc.profit),
        currency=acc.currency,
        leverage=int(acc.leverage),
    )
