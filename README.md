# dbt Assistant

Welcome to your very own dbt Assistant!

The goal of this application is to provide an assistant that can help you perform all (well nearly all :wink:) of your dbt Cloud tasks.  Things like:

- **Querying the Discovery API**
  - What has performance been over the last week for my models owned by the sales group?
  - I made changes to my fact orders model a week ago, was performance impacted since then?
  - What sources are used in my total revenue metric?
- **Querying dbt Docs**
  - How can I build an incremental model?
  - Do you support multi-hop joins in your semantic layer?
  - What's best practice with model naming conventions?
- **Querying the dbt Hub**
  - I have salesforce data, do you have any packages that help with that?
  - I'm more familiar with python testing with great expectations, anything similar?
  - What about packages that deal with data in an S3 bucket?
- **Querying the Semantic Layer**
  - Can you show me total revenue over the last quarter in the U.S.?
  - What values are available for balance segment?
  - Who are the top 5 reps by ARR last quarter?
- **Interacting with the dbt Cloud Admin API**
  - Can you create a webhook for me?
  - When was the last time my job ran in my Analytics project?
  - Can you pull down the manifest for my most recent run?

## Setup

1. Clone this repo locally
2. Create a virtual environment to install dependencies
```sh
python3 -m venv .venv
```
3. Activate your virtual environment
```sh
source .venv/bin/activate
```
4. Install dependencies 
- Using uv:
```sh
uv pip install -r requirements.txt
```
- Without uv:
```sh
pip install -r requirements.txt
```
6. Copy the .env.example file to a .env file and update the environment variables

### Required Env Vars

- `DBT_CLOUD_SERVICE_TOKEN`
- `DBT_CLOUD_ENVIRONMENT_ID`

Additionally, one of `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` is required to initialize the appropriate LLM.

### Optional Env Vars

#### DBT_ASSISTANT_

Use the prefix `DBT_ASSISTANT_` and then common arguments to language models.  As an example, if I had the following in my `.env` file (alongside an `OPENAI_API_KEY`):
```cfg
DBT_ASSISTANT_MODEL=gpt-3.5-turbo
DBT_ASSISTANT_TEMPERATURE=1
DBT_ASSISTANT_BASE_URL=my-base-url.com
```

The LLM would be initialized with the following:
```python
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=1, base_url="my-base-url.com")
```

#### Langchain
The Langchain env vars are optional but if used then the traces will be logged out to Langsmith:
- `LANGCHAIN_API_KEY`
- `LANGCHAIN_TRACING_V2`

#### Pinecone
If using Pinecone for vector storage, make sure you supply that as `PINECONE_API_KEY`.  The lone vector embedding in this application is used to power the data from hub.getdbt.com

#### Tavily
[Tavily](https://tavily.com/) is used as the default tool when doing any internet searches (used for the docs tool).  You can sign up for a free API key [here](https://tavily.us.auth0.com/u/signup?state=hKFo2SA1MEN3T1NrT09uTnV3bHRKSnZqZjI0RzNXYjVRbWc0caFur3VuaXZlcnNhbC1sb2dpbqN0aWTZIG93bmlzOUpGaXM2Zl9kS2dJcmVOY281Q0FOa25hTXFXo2NpZNkgUlJJQXZ2WE5GeHBmVFdJb3pYMW1YcUxueVVtWVNUclE)

If you don't want to use Tavily, a free search tool via `DuckDuckGoSearch` will be used instead.

7. Open the dbt Assistant jupyter notebook
```sh
jupyter notebook
```

The cell at the bottom is where you can begin to ask questions of the dbt Assistant.

## Feedback

Feel free to provide feedback in the form of issues.  PRs welcome!