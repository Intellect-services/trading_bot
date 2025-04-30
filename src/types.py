from typing import Any, Callable, Dict, Optional, Union
from datetime import datetime
from flask import Response
from flask_socketio import SocketIO

# Type aliases for route decorators
RouteDecorator = Callable[..., Response]
SocketIODecorator = Callable[..., None]

# Type aliases for bot metrics and status
BotMetrics = Dict[str, Union[float, int, str, datetime, None]]
BotStatusDict = Dict[str, Union[BotMetrics, bool, str, None]]

# Type aliases for configuration
ConfigDict = Dict[str, Any]

# Type aliases for trading data
PositionDict = Dict[str, Union[str, float, int]]
OrderDict = Dict[str, Union[str, float, int, datetime]]
AccountDict = Dict[str, Union[str, float, int, bool]]

# Type aliases for strategy
StrategyConfig = Dict[str, Any]
StrategyState = Dict[str, Any]

# Type aliases for backtesting
BacktestResult = Dict[str, Union[float, int, str, Dict[str, float]]]
BacktestMetrics = Dict[str, float] 