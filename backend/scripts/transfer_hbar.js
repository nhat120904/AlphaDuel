/**
 * Transfer HBAR between accounts
 * Usage: node transfer_hbar.js <accountId> <privateKey> <toAccountId> <amount> <memo>
 */

const {
  AccountId,
  PrivateKey,
  Client,
  TransferTransaction,
  Hbar
} = require("@hiero-ledger/sdk");

async function main() {
  let client;
  try {
    // Get arguments from command line
    const accountId = process.argv[2];
    const privateKey = process.argv[3];
    const toAccountId = process.argv[4];
    const amount = parseFloat(process.argv[5]);
    const memo = process.argv[6] || "";

    if (!accountId || !privateKey || !toAccountId || !amount) {
      console.error("Usage: node transfer_hbar.js <accountId> <privateKey> <toAccountId> <amount> <memo>");
      process.exit(1);
    }

    // Parse account and key
    const myAccountId = AccountId.fromString(accountId);
    const myPrivateKey = PrivateKey.fromStringECDSA(privateKey);
    const recipientAccountId = AccountId.fromString(toAccountId);

    // Pre-configured client for testnet
    client = Client.forTestnet();
    client.setOperator(myAccountId, myPrivateKey);

    // Create transfer transaction
    let transaction = new TransferTransaction()
      .addHbarTransfer(myAccountId, new Hbar(-amount))
      .addHbarTransfer(recipientAccountId, new Hbar(amount));

    if (memo) {
      transaction = transaction.setTransactionMemo(memo);
    }

    // Execute transaction
    const txResponse = await transaction.execute(client);

    // Get receipt
    const receipt = await txResponse.getReceipt(client);

    // Get transaction ID
    const txId = txResponse.transactionId.toString();

    // Output JSON for Python to parse
    console.log(JSON.stringify({
      success: true,
      transactionId: txId,
      status: receipt.status.toString(),
      amount: amount,
      from: accountId,
      to: toAccountId,
      hashscanUrl: `https://hashscan.io/testnet/transaction/${txId}`
    }));

  } catch (error) {
    console.error(JSON.stringify({
      success: false,
      error: error.message
    }));
    process.exit(1);
  } finally {
    if (client) client.close();
  }
}

main();
