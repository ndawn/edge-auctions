INTENT_SUBSCRIBE_REQUEST_COLD = "Уведомлять об аукционах"
INTENT_UNSUBSCRIBE_REQUEST_COLD = "Не уведомлять об аукционах"

INTENT_SUBSCRIBE_REQUEST = "Подписаться на уведомления об аукционах"
INTENT_UNSUBSCRIBE_REQUEST = "Отписаться от уведомлений об аукционах"

INTENT_SUBSCRIBED = (
    "Вы успешно подписались на уведомления об аукционах! "
    f"Если захотите отписаться, нажмите кнопку \"{INTENT_UNSUBSCRIBE_REQUEST}\". "
    f"Если кнопка по каким-то причинам пропала, напишите \"{INTENT_UNSUBSCRIBE_REQUEST_COLD}\", "
    f"и она появится."
)
INTENT_UNSUBSCRIBED = "Вы успешно отписались от уведомлений об аукционах!"

INTENT_SUBSCRIBED_ALREADY = "Вы уже подписаны на уведомления об аукционах"
INTENT_UNSUBSCRIBED_ALREADY = "Вы не подписаны на уведомления об аукционах"

INTENT_SUBSCRIBE_CALL = f"Чтобы подписаться на уведомления об аукционах, " f"нажмите \"{INTENT_SUBSCRIBE_REQUEST}\""
INTENT_UNSUBSCRIBE_CALL = f"Чтобы отписаться от уведомлений об аукционах, " f"нажмите \"{INTENT_UNSUBSCRIBE_REQUEST}\""

BUYOUT_REQUEST = "Купить сейчас"

BID_BEATEN = "Ставка бита!"
BID_SNIPED = f"{BID_BEATEN}\nОкончание аукциона в %s."
BOUGHT_OUT = "Аукцион выкуплен по цене \"Купить сейчас\"."
INVALID_BID = "Неверная сумма ставки! Ставка была удалена."
INVALID_BUYOUT = "Объём ставок превысил порог выкупа. Выкуп недоступен."
COMMENT_SUBSCRIBE_CALL = (
    "Подпишитесь на уведомления об аукционах, иначе мы не сможем оповестить вас в случае выигрыша. "
    "Для этого напишите нам в сообщения \"Уведомлять об аукционах\" или нажмите соответствующую кнопку, "
    "если она отображается."
)
UNABLE_TO_NOTIFY_WINNER = "Пожалуйста, свяжитесь с нами в сообщениях сообщества для получения выигрыша."
