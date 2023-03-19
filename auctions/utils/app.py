from flask import Flask as BaseFlask

from auctions.dependencies import DependencyProvider


class Flask(BaseFlask):
    provider: DependencyProvider
