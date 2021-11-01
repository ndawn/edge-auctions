def bid_beaten() -> str:
    return 'Ставка бита!'


def bid_sniped(due: str) -> str:
    return f'Ставка бита!\nОкончание аукциона в {due}'


def invalid_bid() -> str:
    return 'Неверная сумма ставки! Ставка была удалена.'


def winner_message(user_name: str, auction_links: str, overall_price: str) -> str:
    return (
        f'Привет, {user_name}!\n'
        'Поздравляем с победой в аукционах!\n\n'
        f'Выигранные аукционы:\n{auction_links}\n\n'
        f'К оплате за лот: {overall_price} рублей\n\n'
        'Напишите, пожалуйста, нужно ли списывать Плюсы и совершать доставку, или нет. '
        'После этого мы скинем информацию по оплате.'
    )


def buyout_expired(price: str) -> str:
    return f'Сумма последней ставки достигла порога в {price} рублей, поэтому выкуп недоступен.'


def auction_closed() -> str:
    return 'Аукцион закрыт!'


def not_subscribed() -> str:
    return (
        'Подпишитесь на уведомления об аукционах, иначе мы не сможем оповестить вас в случае выигрыша. '
        'Для этого напишите нам в сообщения "Уведомлять об аукционах" или нажмите соответствующую кнопку, '
        'если она отображается.'
    )


def auction_buyout() -> str:
    return 'Лот выкуплен по цене "Купить сейчас".'
