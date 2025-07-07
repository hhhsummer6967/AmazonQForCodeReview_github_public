import json
import logging
import os
import boto3
import re
from ewallet.repository.dynamodb_wallet_repository import DynamoDbWalletRepository
from ewallet.repository.dynamodb_transaction_repository import DynamoDbTransactionRepository
from ewallet.repository.transaction_repository import TransactionRepository
from ewallet.repository.base_repository import BaseRepository
from ewallet.model.wallet import Wallet
from ewallet.model.transaction import Transaction, TransactionType

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_wallet_repository(dynamodb_client, table_name) -> BaseRepository:
    return DynamoDbWalletRepository(dynamodb_client, table_name)

def get_transaction_repository(dynamodb_client, table_name) -> TransactionRepository:
    return DynamoDbTransactionRepository(dynamodb_client, table_name)

def find_wallet(dynamodb_client, wallet_table_name, wallet_id) -> Wallet:
    wallet_repository = get_wallet_repository(dynamodb_client, wallet_table_name)
    return wallet_repository.find(wallet_id)

def save_transaction(dynamodb_client, transaction_table_name, transaction) -> str:
    transaction_repository = get_transaction_repository(dynamodb_client, transaction_table_name)
    return transaction_repository.save(transaction)

def validate_payload(payload) -> list[str]:
    """
    Validate whether the mandatory fields are present in the payload.
    The mandatory fields are wallet_id, currency and amount.
    The amount must be a positive number with 2 decimals.
    The currency must be a valid ISO 4217 currency code.
    """
    errors = []
    
    if 'wallet_id' not in payload:
        errors.append('wallet_id is missing')
    
    if 'amount' not in payload:
        errors.append('amount is missing')
    elif not re.match(r'^[0-9]+\.[0-9]{2}$', str(payload['amount'])):
        errors.append('Invalid amount format')
    elif float(payload['amount']) <= 0:
        errors.append('Amount must be positive')
    
    if 'currency' not in payload:
        errors.append('currency is missing')
    elif not Transaction.is_valid_currency_code(payload['currency']):
        errors.append('Invalid currency code')
    
    return errors

def lambda_handler(event, context):
    try:
        logger.info('Event: {}'.format(event))
        
        wallet_table_name = os.getenv('WALLETS_TABLE')
        transaction_table_name = os.getenv('TRANSACTIONS_TABLE')
        
        if not wallet_table_name or not transaction_table_name:
            raise Exception('Table names missing')
        
        try:
            payload = json.loads(event['body'])
        except Exception:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Bad Request'})
            }
        
        # Validate payload
        validation_errors = validate_payload(payload)
        if validation_errors:
            return {
                'statusCode': 400,
                'body': json.dumps({'message': 'Validation failed', 'errors': validation_errors})
            }
        
        dynamodb_client = boto3.client('dynamodb')
        
        # Find wallet
        wallet = find_wallet(dynamodb_client, wallet_table_name, payload['wallet_id'])
        if not wallet:
            return {
                'statusCode': 404,
                'body': json.dumps({'message': 'Wallet not found'})
            }
        
        # Create top-up transaction
        amount = float(payload['amount'])
        currency = payload['currency']
        
        transaction = Transaction(wallet, amount, currency, TransactionType.TOP_UP)
        transaction_id = save_transaction(dynamodb_client, transaction_table_name, transaction)
        
        # Update wallet balance
        wallet.top_up(amount, currency)
        wallet_repository = get_wallet_repository(dynamodb_client, wallet_table_name)
        wallet_repository.save(wallet)
        
        response = {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Top-up successful',
                'transaction_id': transaction_id,
                'wallet_id': wallet.id,
                'amount': amount,
                'currency': currency,
                'new_balance': wallet.get_balance(currency)
            })
        }
        
        logger.info("Response: %s", response)
        return response
        
    except Exception as error:
        logger.error('Error: {}'.format(error))
        return {
            'statusCode': 500,
            'body': json.dumps({'message': 'Internal server error'})
        }