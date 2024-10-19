import requests
import json
from web3 import Web3

# URL для подключения к Ethereum через Infura (замените на ваш Project ID)
infura_url = "https://arbitrum-sepolia.infura.io/v3/446dd1352b4042a4a9c905d676d8991b"
web3 = Web3(Web3.HTTPProvider(infura_url))

# Проверим подключение через web3
if not web3.is_connected():
    print("Ошибка подключения к Infura через Web3.")
    exit()

# ABI контракта USDC (вставьте полный ABI, скопированный с Etherscan)
contract_abi = json.loads('''[{"constant":false,"inputs":[{"name":"newImplementation","type":"address"}],
"name":"upgradeTo","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,
"inputs":[{"name":"newImplementation","type":"address"},{"name":"data","type":"bytes"}],"name":"upgradeToAndCall",
"outputs":[],"payable":true,"stateMutability":"payable","type":"function"},{"constant":true,"inputs":[],
"name":"implementation","outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view",
"type":"function"},{"constant":false,"inputs":[{"name":"newAdmin","type":"address"}],"name":"changeAdmin","outputs":[
],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":true,"inputs":[],"name":"admin",
"outputs":[{"name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"inputs":[{
"name":"_implementation","type":"address"}],"payable":false,"stateMutability":"nonpayable","type":"constructor"},
{"payable":true,"stateMutability":"payable","type":"fallback"},{"anonymous":false,"inputs":[{"indexed":false,
"name":"previousAdmin","type":"address"},{"indexed":false,"name":"newAdmin","type":"address"}],"name":"AdminChanged",
"type":"event"},{"anonymous":false,"inputs":[{"indexed":false,"name":"implementation","type":"address"}],
"name":"Upgraded","type":"event"}]''')

# Адрес контракта USDC
contract_address = '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48'
contract = web3.eth.contract(address=contract_address, abi=contract_abi)


# Функция для проверки подключения к Infura
def check_infura_connection():
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_blockNumber",
        "params": [],
        "id": 1
    }
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(infura_url, json=payload, headers=headers)
        if response.status_code == 200:
            latest_block = int(response.json()['result'], 16)
            print(f"Подключение успешно! Номер последнего блока: {latest_block}")
            return latest_block
        else:
            print(f"Ошибка подключения. Код ответа: {response.status_code}, Текст ошибки: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return None


# Функция для получения логов контракта
def get_contract_events(from_block, to_block, topic):
    payload = {
        "jsonrpc": "2.0",
        "method": "eth_getLogs",
        "params": [{
            "fromBlock": hex(from_block),  # Убедимся, что блоки в формате 0x
            "toBlock": hex(to_block),
            "address": Web3.toChecksumAddress(contract_address),  # Преобразуем адрес контракта
            "topics": [topic]
        }],
        "id": 1
    }
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(infura_url, json=payload, headers=headers)
        if response.status_code == 200:
            response_json = response.json()
            if 'result' in response_json:
                return response_json['result']
            else:
                print("Ошибка: 'result' отсутствует в ответе.")
                print("Полный ответ: ", response_json)
                return []
        else:
            print(f"Ошибка получения событий. Код ответа: {response.status_code}, Текст ошибки: {response.text}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return []


# Функция для парсинга событий Transfer
def parse_transfer_events(events):
    for event in events:
        tx_hash = event['transactionHash']
        from_address = web3.toChecksumAddress(Web3.toHex(event['topics'][1]))  # Преобразуем адрес
        to_address = web3.toChecksumAddress(Web3.toHex(event['topics'][2]))  # Преобразуем адрес
        value = int(event['data'], 16)  # Значение перевода в wei
        decimals = contract.functions.decimals().call()  # Получаем количество знаков после запятой для токена
        print(f"Транзакция: {tx_hash}")
        print(f"  Отправитель: {from_address}")
        print(f"  Получатель: {to_address}")
        print(f"  Сумма: {value / 10 ** decimals} токенов")
        print("-" * 40)


# Основная функция
def main():
    latest_block = check_infura_connection()
    if latest_block:
        from_block = latest_block - 10
        to_block = latest_block
        topic_transfer = Web3.keccak(text="Transfer(address,address,uint256)").hex()
        print(f"Диапазон блоков: от {hex(from_block)} до {hex(to_block)}")
        print(f"Адрес контракта: {contract_address}")
        print(f"Топик события Transfer: {topic_transfer}")
        events = get_contract_events(from_block, to_block, topic_transfer)
        if events:
            parse_transfer_events(events)
        else:
            print("События не найдены в указанном диапазоне блоков.")
    try:
        token_name = contract.functions.name().call()
        print(f"Название токена: {token_name}")
    except Exception as e:
        print(f"Ошибка вызова функции контракта: {e}")
    try:
        token_symbol = contract.functions.symbol().call()
        print(f"Символ токена: {token_symbol}")
    except Exception as e:
        print(f"Ошибка вызова символа токена: {e}")


# Запуск программы
if __name__ == "__main__":
    main()
