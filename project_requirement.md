# Project Name: AlphaDuel

### *The On-Chain AI Debate Arena with "Skin in the Game"*

## 1\. Executive Summary

**AlphaDuel** is a multi-agent analytical platform that gamifies cryptocurrency market analysis. Instead of a standard chatbot, AlphaDuel deploys competing AI agents—a "Bull" and a "Bear"—to debate market trends in real-time.

The core innovation is **Accountability**. The system utilizes the **Hedera Blockchain** to record predictions and programmatically wager HBAR tokens based on the AI's confidence level. This introduces the concept of "Skin in the Game" to AI financial advice, solving the problem of AI hallucination and lack of trust.

## 2\. Core Concept

  * **The Problem:** Traditional AI financial assistants provide generic advice with zero cost for being wrong. Users struggle to trust "black box" algorithms.
  * **The Solution:** An observable debate between specialized agents where the winner must back their prediction with actual value (Testnet HBAR) on an immutable ledger.

## 3\. Technical Architecture

The system follows a decoupled architecture separating the User Interface (Next.js) from the Agent Logic (Python/FastAPI).

### The Stack

  * **Frontend:** **Next.js** + **Vercel AI SDK** (React) for a high-performance, streaming chat interface.
  * **Backend:** **FastAPI** (Python) to serve as the API gateway.
  * **Agent Orchestration:** **LangGraph** to manage the stateful workflow, cyclic dependencies, and memory between agents.
  * **Blockchain Layer:** **Hedera SDK (Python)** for Consensus Service (HCS) logging and Cryptocurrency Service for wagering.

## 4\. System Workflow (Step-by-Step)

Here is how data flows through the system when a user asks a question:

### Phase 1: User Intent & Data Retrieval

1.  **User Input:** The user enters a query via the Vercel AI SDK frontend (e.g., *"What is the outlook for HBAR today?"*).
2.  **API Call:** The frontend sends the prompt to the FastAPI backend.
3.  **Graph Initialization:** FastAPI initializes a **LangGraph StateGraph**.
4.  **Market Data Node:** The first node in the graph fetches real-time data (Price, Volume, RSI, News) using external APIs (CoinGecko/Tavily).

### Phase 2: The Multi-Agent Debate (LangGraph Loop)

5.  **Bull Agent Node:** Analyzes the data specifically looking for upside potential. It generates a "Bullish Argument" (e.g., highlighting increasing volume).
6.  **Bear Agent Node:** Analyzes the same data looking for downside risks. It generates a "Bearish Argument" (e.g., highlighting overbought RSI).
7.  **Debate Loop:** Using LangGraph, these agents can optionally challenge each other's points 1-2 times to refine their arguments.

### Phase 3: The Verdict & On-Chain Action

8.  **Referee Agent Node:** Evaluates the arguments from both sides. It determines:
      * The Winner (Bull or Bear).
      * The Confidence Score (0-100%).
      * The Wager Amount (calculated based on confidence).
9.  **Hedera Action (The "Skin in the Game"):**
      * **Log:** The system uses **Hedera Consensus Service (HCS)** to write the debate summary and prediction to a public topic. This creates an immutable audit trail.
      * **Bet:** The system uses the **Hedera Crypto Service** to transfer the calculated amount of HBAR from the Agent's Wallet to a "Locked/Escrow" address on the Testnet.

### Phase 4: Response Streaming

10. **Stream to UI:** The entire process (Agent thoughts, arguments, and final verdict) is streamed back to the Vercel AI SDK frontend.
11. **Verification:** The frontend renders a "Transaction Card" showing the **Hedera Transaction Hash** link (pointing to HashScan), proving the AI actually executed the wager.

## 5\. Detailed Component Breakdown

### A. Frontend (Vercel AI SDK)

  * **`useChat` / `useObject` Hook:** Manages the chat state and handles the stream from FastAPI.
  * **Custom Components:**
      * `<BullBubble />`: Green-themed message bubble for the optimist agent.
      * `<BearBubble />`: Red-themed message bubble for the pessimist agent.
      * `<RefereeCard />`: A distinct component displaying the final verdict and the Hedera Transaction link.

### B. Backend (FastAPI + LangGraph)

  * **State Schema:** A typed dictionary maintains the context (example):
    ```python
    class AgentState(TypedDict):
        symbol: str
        market_data: dict
        bull_opinion: str
        bear_opinion: str
        winner: Literal["Bull", "Bear"]
        tx_id: str
    ```
  * **Nodes:** Separate Python functions for `run_bull_agent`, `run_bear_agent`, `run_referee`, and `execute_hedera_tx`.

### C. Blockchain (Hedera)

  * **Consensus Service (HCS):** Used as a decentralized "Truth Log." Even if the database is deleted, the AI's prediction history remains on-chain.
  * **Testnet Implementation:** The project will use a funded Hedera Testnet account to simulate the financial risk without using real money during the hackathon.

## 6\. Key Differentiators (Hackathon Winning Points)

1.  **Complexity via LangGraph:** It demonstrates advanced usage of AI agents (reasoning + debating) rather than simple Retrieval Augmented Generation (RAG).
2.  **Hedera Native Integration:** It doesn't just "talk" about crypto; it interacts with the ledger. It uses HCS for transparency and crypto transfers for gamification.
3.  **User Experience:** The "Debate" format provides a balanced view of the market, which is more valuable to investors than a single biased answer.