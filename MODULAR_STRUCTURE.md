# Modular Order Executor Trading Bot

This document describes the modular structure of the Order Executor trading bot.

## 📁 Project Structure

```
Order_Executor/
├── main.py                 # Main entry point
├── main_original.py        # Backup of original monolithic code
├── config.py              # Configuration and credentials management
├── api_client.py          # Shoonya API wrapper
├── trade_logger.py        # Trade logging and CSV operations
├── trading_engine.py      # Core trading logic and order management
├── websocket_handler.py   # Real-time data processing
├── telegram_bot.py        # Telegram bot handlers and conversations
├── api_helper.py          # Original Shoonya API helper (unchanged)
├── credentials.json       # API credentials (not in repo)
├── requirements.txt       # Python dependencies
└── trade_log.csv         # Trade history log (auto-generated)
```

## 🏗️ Module Descriptions

### 1. `config.py` - Configuration Management
- **Purpose**: Centralized configuration and credentials management
- **Key Features**:
  - Loads credentials from JSON file
  - Manages global settings and constants
  - Handles API configuration setup
  - Provides conversation states for Telegram bot

### 2. `api_client.py` - API Client
- **Purpose**: Wrapper for Shoonya API operations
- **Key Features**:
  - Login/logout functionality
  - Order placement and management
  - Market data retrieval
  - Symbol search functionality
  - Subscription management

### 3. `trade_logger.py` - Trade Logging
- **Purpose**: Handles trade logging and CSV operations
- **Key Features**:
  - CSV file management
  - Trade entry/exit logging
  - Trade history retrieval
  - PnL calculations
  - Statistics generation

### 4. `trading_engine.py` - Trading Engine
- **Purpose**: Core trading logic and order management
- **Key Features**:
  - Order placement with risk management
  - Trade monitoring and exit strategies
  - SL/Target hit detection
  - Trade statistics and reporting
  - Active trade management

### 5. `websocket_handler.py` - WebSocket Handler
- **Purpose**: Real-time data processing and market updates
- **Key Features**:
  - WebSocket callback management
  - Real-time price updates
  - Order update processing
  - Trade condition monitoring

### 6. `telegram_bot.py` - Telegram Bot
- **Purpose**: User interaction and conversation handling
- **Key Features**:
  - Command handlers (/start, /status, /m, /help)
  - Conversation flow management
  - Symbol selection interface
  - Trade management interface
  - User input validation
  - Trade notifications
  - Active trade modification (SL, Target, Exit)

### 7. `main.py` - Main Entry Point
- **Purpose**: Application initialization and orchestration
- **Key Features**:
  - Module initialization
  - Dependency injection
  - Error handling
  - Application startup

## 🔄 Data Flow

1. **Initialization**: `main.py` initializes all modules with proper dependencies
2. **User Input**: Telegram bot receives user commands and trading parameters
3. **Order Placement**: Trading engine places orders through API client
4. **Real-time Monitoring**: WebSocket handler monitors market data
5. **Trade Management**: Trading engine manages exits based on SL/Target
6. **Logging**: Trade logger records all trade activities
7. **Notifications**: Telegram bot sends updates to users

## 🚀 Benefits of Modular Structure

### 1. **Separation of Concerns**
- Each module has a single responsibility
- Easier to understand and maintain
- Clear boundaries between different functionalities

### 2. **Reusability**
- Modules can be reused in other projects
- API client can be used independently
- Trading engine can be adapted for different interfaces

### 3. **Testability**
- Each module can be unit tested independently
- Mock dependencies for isolated testing
- Easier to debug specific functionality

### 4. **Maintainability**
- Changes to one module don't affect others
- Easier to add new features
- Clear code organization

### 5. **Scalability**
- Easy to add new trading strategies
- Can support multiple exchanges
- Can add different notification channels

## 🔧 Usage

### Running the Bot
```bash
python main.py
```

### Available Commands
- `/start` - Begin trading setup
- `/status` - View trading statistics
- `/trades` - View active trades with current PnL
- `/m` - Modify active trades (SL, Target, Exit)
- `/help` - Show help message

### Trade Management Flow
1. **View Active Trades**: Use `/m` command
2. **Select Trade**: Choose from the list of active trades
3. **Choose Action**:
   - 📉 **Modify SL**: Update stoploss percentage
   - 🎯 **Modify Target**: Update target percentage
   - 🚪 **Exit Trade**: Manually exit the trade
   - ❌ **Cancel**: Abort modification

### Adding New Features
1. **New Trading Strategy**: Add methods to `trading_engine.py`
2. **New API Endpoint**: Add methods to `api_client.py`
3. **New Bot Command**: Add handlers to `telegram_bot.py`
4. **New Logging Format**: Modify `trade_logger.py`

### Configuration
- Update `credentials.json` with your API credentials
- Modify constants in `config.py` for different settings
- Adjust trading parameters in `trading_engine.py`

## 🛠️ Dependencies

All dependencies are listed in `requirements.txt`:
- `requests` - HTTP requests
- `websocket_client` - WebSocket connections
- `pandas` - Data analysis
- `pyyaml` - YAML parsing
- `pyotp` - Two-factor authentication
- `retrying` - Retry mechanisms
- `python-telegram-bot` - Telegram bot API
- `NorenRestApiPy` - Shoonya API wrapper

## 📝 Notes

- The original monolithic code is preserved in `main_original.py`
- All modules maintain the same functionality as the original
- The modular structure makes the code more professional and maintainable
- Each module can be easily extended or modified without affecting others
