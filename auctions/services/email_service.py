# from string import Template
#
# from flask_mail import Mail
# from flask_mail import Message
#
# from auctions.config import Config
# from auctions.db.models.enum import EmailType
# from auctions.db.models.users import User
# from auctions.dependencies import Provide
#
#
# class EmailService:
#     def __init__(self, mail: Mail = Provide(), config: Config = Provide()) -> None:
#         self.mail = mail
#         self.config = config
#
#     def get_message_template(self, message_type: EmailType) -> str:
#         file_path = self.config.email_templates_path / f"{message_type.value}.html"
#
#         with open(file_path) as template_file:
#             return template_file.read()
#
#     @staticmethod
#     def populate_template(template: str, recipient: User) -> str:
#         return Template(template).substitute(
#             first_name=recipient.first_name,
#             last_name=recipient.last_name,
#         )
#
#     def send_email(self, recipient: User, message_type: EmailType) -> None:
#         template = self.get_message_template(message_type)
#         template = self.populate_template(template, recipient)
#
#         message = Message(
#             subject=self.config.email_subject,
#             sender=self.config.email_sender,
#             recipients=[recipient.email],
#             html=template,
#         )
#         self.mail.send(message)
