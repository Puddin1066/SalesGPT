import json
import os

import boto3
import requests
try:
    from langchain.agents import Tool
except ImportError:
    try:
        # Fallback for langchain 0.1.0 - try langchain_community
        from langchain_community.tools import Tool
    except ImportError:
        try:
            # Try langchain_core.tools
            from langchain_core.tools import Tool
        except ImportError:
            # Create a simple Tool class as last resort
            from typing import Callable
            class Tool:
                def __init__(self, name: str, func: Callable, description: str):
                    self.name = name
                    self.func = func
                    self.description = description
# RetrievalQA - try multiple import paths for compatibility
try:
    from langchain.chains import RetrievalQA
except ImportError:
    try:
        from langchain.chains.retrieval_qa.base import RetrievalQA
    except ImportError:
        try:
            # Newer langchain versions - create a placeholder
            RetrievalQA = None
            import warnings
            warnings.warn("RetrievalQA not available - knowledge base functionality will be limited")
        except:
            RetrievalQA = None

# Text splitter - try multiple import paths
try:
    from langchain.text_splitter import CharacterTextSplitter
except ImportError:
    try:
        from langchain_text_splitters import CharacterTextSplitter
    except ImportError:
        # Fallback - create simple splitter
        class CharacterTextSplitter:
            def __init__(self, chunk_size=5000, chunk_overlap=200):
                self.chunk_size = chunk_size
                self.chunk_overlap = chunk_overlap
            def split_text(self, text):
                # Simple chunking
                chunks = []
                for i in range(0, len(text), self.chunk_size - self.chunk_overlap):
                    chunks.append(text[i:i+self.chunk_size])
                return chunks
from langchain_community.chat_models import BedrockChat, ChatLiteLLM
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from litellm import completion
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def setup_knowledge_base(
    product_catalog: str = None, model_name: str = "gpt-3.5-turbo"
):
    """
    We assume that the product catalog is simply a text string.
    """
    # load product catalog
    with open(product_catalog, "r") as f:
        product_catalog = f.read()

    text_splitter = CharacterTextSplitter(chunk_size=5000, chunk_overlap=200)
    texts = text_splitter.split_text(product_catalog)

    llm = ChatLiteLLM(model_name="gpt-4-0125-preview", temperature=0)

    try:
        embeddings = OpenAIEmbeddings()
    except Exception as e:
        raise RuntimeError(
            "OpenAIEmbeddings failed (common cause: openai>=1.55 with langchain-openai==0.0.2). "
            "Fix: `pip install 'openai>=1.7,<1.55'` or upgrade langchain-openai, "
            "or leave SALESGPT_USE_TOOLS=false (default) if you do not need product-catalog search. "
            f"Original error: {e}"
        ) from e

    docsearch = Chroma.from_texts(
        texts, embeddings, collection_name="product-knowledge-base"
    )

    if RetrievalQA is None:
        # Fallback for newer langchain versions
        # Return a simple retriever wrapper
        class SimpleRetriever:
            def __init__(self, retriever):
                self.retriever = retriever
            def run(self, query):
                docs = self.retriever.get_relevant_documents(query)
                return docs[0].page_content if docs else ""
        
        return SimpleRetriever(docsearch.as_retriever())
    
    knowledge_base = RetrievalQA.from_chain_type(
        llm=llm, chain_type="stuff", retriever=docsearch.as_retriever()
    )
    return knowledge_base


def completion_bedrock(model_id, system_prompt, messages, max_tokens=1000):
    """
    High-level API call to generate a message with Anthropic Claude.
    """
    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime", region_name=os.environ.get("AWS_REGION_NAME")
    )

    body = json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": messages,
        }
    )

    response = bedrock_runtime.invoke_model(body=body, modelId=model_id)
    response_body = json.loads(response.get("body").read())

    return response_body


def get_product_id_from_query(query, product_price_id_mapping_path):
    # Load product_price_id_mapping from a JSON file
    with open(product_price_id_mapping_path, "r") as f:
        product_price_id_mapping = json.load(f)

    # Serialize the product_price_id_mapping to a JSON string for inclusion in the prompt
    product_price_id_mapping_json_str = json.dumps(product_price_id_mapping)

    # Dynamically create the enum list from product_price_id_mapping keys
    enum_list = list(product_price_id_mapping.values()) + [
        "No relevant product id found"
    ]
    enum_list_str = json.dumps(enum_list)

    prompt = f"""
    You are an expert data scientist and you are working on a project to recommend products to customers based on their needs.
    Given the following query:
    {query}
    and the following product price id mapping:
    {product_price_id_mapping_json_str}
    return the price id that is most relevant to the query.
    ONLY return the price id, no other text. If no relevant price id is found, return 'No relevant price id found'.
    Your output will follow this schema:
    {{
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Price ID Response",
    "type": "object",
    "properties": {{
        "price_id": {{
        "type": "string",
        "enum": {enum_list_str}
        }}
    }},
    "required": ["price_id"]
    }}
    Return a valid directly parsable json, dont return in it within a code snippet or add any kind of explanation!!
    """
    prompt += "{"
    model_name = os.getenv("GPT_MODEL", "gpt-3.5-turbo-1106")

    if "anthropic" in model_name:
        response = completion_bedrock(
            model_id=model_name,
            system_prompt="You are a helpful assistant.",
            messages=[{"content": prompt, "role": "user"}],
            max_tokens=1000,
        )

        product_id = response["content"][0]["text"]

    else:
        response = completion(
            model=model_name,
            messages=[{"content": prompt, "role": "user"}],
            max_tokens=1000,
            temperature=0,
        )
        product_id = response.choices[0].message.content.strip()
    return product_id


def generate_stripe_payment_link(query: str) -> str:
    """Generate a stripe payment link for a customer based on a single query string."""

    # example testing payment gateway url
    PAYMENT_GATEWAY_URL = os.getenv(
        "PAYMENT_GATEWAY_URL", "https://agent-payments-gateway.vercel.app/payment"
    )
    PRODUCT_PRICE_MAPPING = os.getenv(
        "PRODUCT_PRICE_MAPPING", "example_product_price_id_mapping.json"
    )

    # use LLM to get the price_id from query
    price_id = get_product_id_from_query(query, PRODUCT_PRICE_MAPPING)
    price_id = json.loads(price_id)
    payload = json.dumps(
        {"prompt": query, **price_id, "stripe_key": os.getenv("STRIPE_API_KEY")}
    )
    headers = {
        "Content-Type": "application/json",
    }

    response = requests.request(
        "POST", PAYMENT_GATEWAY_URL, headers=headers, data=payload
    )
    return response.text

def get_mail_body_subject_from_query(query):
    prompt = f"""
    Given the query: "{query}", analyze the content and extract the necessary information to send an email. The information needed includes the recipient's email address, the subject of the email, and the body content of the email. 
    Based on the analysis, return a dictionary in Python format where the keys are 'recipient', 'subject', and 'body', and the values are the corresponding pieces of information extracted from the query. 
    For example, if the query was about sending an email to notify someone of an upcoming event, the output should look like this:
    {{
        "recipient": "example@example.com",
        "subject": "Upcoming Event Notification",
        "body": "Dear [Name], we would like to remind you of the upcoming event happening next week. We look forward to seeing you there."
    }}
    Now, based on the provided query, return the structured information as described.
    Return a valid directly parsable json, dont return in it within a code snippet or add any kind of explanation!!
    """
    model_name = os.getenv("GPT_MODEL", "gpt-3.5-turbo-1106")

    if "anthropic" in model_name:
        response = completion_bedrock(
            model_id=model_name,
            system_prompt="You are a helpful assistant.",
            messages=[{"content": prompt, "role": "user"}],
            max_tokens=1000,
        )

        mail_body_subject = response["content"][0]["text"]

    else:
        response = completion(
            model=model_name,
            messages=[{"content": prompt, "role": "user"}],
            max_tokens=1000,
            temperature=0.2,
        )
        mail_body_subject = response.choices[0].message.content.strip()
    print(mail_body_subject)
    return mail_body_subject

def send_email_with_gmail(email_details):
    '''.env should include GMAIL_MAIL and GMAIL_APP_PASSWORD to work correctly'''
    try:
        sender_email = os.getenv("GMAIL_MAIL")
        app_password = os.getenv("GMAIL_APP_PASSWORD")
        recipient_email = email_details["recipient"]
        subject = email_details["subject"]
        body = email_details["body"]
        # Create MIME message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Create server object with SSL option
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(sender_email, app_password)
        text = msg.as_string()
        server.sendmail(sender_email, recipient_email, text)
        server.quit()
        return "Email sent successfully."
    except Exception as e:
        return f"Email was not sent successfully, error: {e}"

def send_email_tool(query):
    '''Sends an email based on the single query string'''
    email_details = get_mail_body_subject_from_query(query)
    if isinstance(email_details, str):
        email_details = json.loads(email_details)  # Ensure it's a dictionary
    print("EMAIL DETAILS")
    print(email_details)
    result = send_email_with_gmail(email_details)
    return result


def generate_calendly_invitation_link(query):
    '''Generate a calendly invitation link based on the single query string'''
    event_type_uuid = os.getenv("CALENDLY_EVENT_UUID")
    api_key = os.getenv('CALENDLY_API_KEY')
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    url = 'https://api.calendly.com/scheduling_links'
    payload = {
    "max_event_count": 1,
    "owner": f"https://api.calendly.com/event_types/{event_type_uuid}",
    "owner_type": "EventType"
    }
    
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 201:
        data = response.json()
        return f"url: {data['resource']['booking_url']}"
    else:
        return "Failed to create Calendly link: "

def get_visibility_audit(query: str) -> str:
    """Useful for when you need to check a business's visibility in AI search compared to competitors."""
    from services.visibility import GEMflushAgent
    try:
        # Expected query: "company_id, competitor_name"
        parts = [p.strip() for p in query.split(",")]
        company_id = parts[0]
        competitor_name = parts[1] if len(parts) > 1 else os.getenv("DEFAULT_COMPETITOR", "local competitors")
        
        agent = GEMflushAgent()
        comparison = agent.get_competitor_comparison(company_id, competitor_name)
        
        if "error" in comparison:
            return f"Could not retrieve audit for {company_id}: {comparison['error']}"
            
        return agent.format_evidence_message(comparison, include_full_audit=True)
    except Exception as e:
        return f"Error retrieving visibility audit: {str(e)}"

def lead_research(query: str) -> str:
    """Useful for when you need to research a lead's background or company details."""
    from services.apollo import ApolloAgent
    try:
        # Expected query: email
        agent = ApolloAgent()
        # This is a simplified search - in real use, we'd search by email
        # For now, we search by keywords to get enrichment
        leads = agent.search_leads(geography="", specialty=query, limit=1)
        if not leads:
            return f"No information found for {query}"
        
        lead = leads[0]
        return (
            f"Lead: {lead.name}\n"
            f"Company: {lead.company_name}\n"
            f"Specialty: {lead.specialty}\n"
            f"Website: {lead.website}\n"
            f"Title: {lead.metadata.get('title', 'N/A')}\n"
            f"Employee Count: {lead.metadata.get('employee_count', 0)}"
        )
    except Exception as e:
        return f"Error researching lead: {str(e)}"

def get_tools(product_catalog):
    # query to get_tools can be used to be embedded and relevant tools found
    # see here: https://langchain-langchain.vercel.app/docs/use_cases/agents/custom_agent_with_plugin_retrieval#tool-retriever

    # we only use four tools for now, but this is highly extensible!
    knowledge_base = setup_knowledge_base(product_catalog)
    tools = [
        Tool(
            name="ProductSearch",
            func=knowledge_base.run,
            description="useful for when you need to answer questions about product information or services offered, availability and their costs.",
        ),
        Tool(
            name="GeneratePaymentLink",
            func=generate_stripe_payment_link,
            description="useful to close a transaction with a customer. You need to include product name and quantity and customer name in the query input.",
        ),
        Tool(
            name="SendEmail",
            func=send_email_tool,
            description="Sends an email based on the query input. The query should specify the recipient, subject, and body of the email.",
        ),
        Tool(
            name="SendCalendlyInvitation",
            func=generate_calendly_invitation_link,
            description='''Useful for when you need to create invite for a personal meeting in Sleep Heaven shop. 
            Sends a calendly invitation based on the query input.''',
        ),
        Tool(
            name="GetVisibilityAudit",
            func=get_visibility_audit,
            description="Useful for when you need to check a business's visibility in AI search compared to competitors. Input should be 'company_name, competitor_name' or just 'company_name'.",
        ),
        Tool(
            name="LeadResearch",
            func=lead_research,
            description="Useful for when you need to research a lead's background or company details. Input should be the company name or email.",
        )
    ]

    return tools
