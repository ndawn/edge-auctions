import re


def to_snake_case(name):
    name = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
    name = re.sub("__([A-Z])", r"_\1", name)
    name = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", name)
    return name.lower()


def winner_message(user_name: str, auction_links: list[str], overall_price: int) -> str:
    greet_line = f"Привет, {user_name}!"

    if not user_name:
        greet_line = "Привет!"

    auction_links_joined = "\n".join(auction_links)

    return (
        f"{greet_line}\n"
        "Поздравляем с победой в аукционах!\n\n"
        f"Выигранные аукционы:\n{auction_links_joined}\n\n"
        f"К оплате за лоты: {overall_price} рублей\n\n"
        "Напишите, пожалуйста, нужно ли списывать Плюсы и совершать доставку, или нет. "
        "Мы пришлём ссылку через сутки - после её получения списать Плюсы будет нельзя."
    )


def build_photo_url(photo_id: int, owner_id: int) -> str:
    return f"https://vk.com/photo{owner_id}_{photo_id}"
