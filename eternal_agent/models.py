from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Callable, Any
from enum import Enum
import json 
import uuid

def random_uuid() -> str:
    return str(uuid.uuid4().hex)

class Serializable(object):
    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return json.dumps(self.__dict__())

class ToolParamDtype(str, Enum):
    STRING = "string"
    NUMBER = "number"

class ToolParam(BaseModel):
    name: str
    default_value: Optional[str] = None
    dtype: ToolParamDtype
    description: str

class Tool(BaseModel):
    name: str
    description: str
    param_spec: List[ToolParam]
    executor: Callable
    
    def prototype(self):
        params_str = ', '.join([f"{param.name}: {param.dtype.value}" 
                                for param in self.param_spec])
        
        return f'{self.name}({params_str}) -> {ToolParamDtype.STRING.value}: Takes {len(self.param_spec)} parameters, {self.description}'

class ClassRegistration(BaseModel):
    name: str
    init_params: Dict[str, Any]

class InferenceState(str, Enum):
    EXECUTING = "executing"
    DONE = "done"
    ERROR = "error"

class ReactChainState(str, Enum):
    NEW = "new"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"

class ReactAgentReasoningLog(BaseModel):
    # auto
    id: str = Field(default_factory=lambda: f"fun-{random_uuid()}")

    # for request
    system_prompt: str # personality of the agent
    task: str # set a goal for the agent
    system_reminder: str # set a goal for the agent
    interval_minutes: int = 120

    toolset_cfg: List[ClassRegistration]
    llm_cfg: ClassRegistration

    # for response
    infer_receipt: Optional[str] = None
    state: ReactChainState = ReactChainState.NEW
    scratchpad: List[Dict[str, str]] = []
    system_message: str = "" # for error messages

    def is_done(self):
        return self.state == ReactChainState.DONE

    def is_error(self):
        return self.state == ReactChainState.ERROR

    def clone(self) -> dict:
        return dict(
            id=self.id,
            task=self.task,
            system_reminder=self.system_reminder,
            system_prompt=self.system_prompt,
            interval_minutes=self.interval_minutes,
            infer_receipt=self.infer_receipt,
            state=self.state,
            scratchpad=self.scratchpad,
            system_message=self.system_message,
            toolset_cfg=[e.model_dump() for e in self.toolset_cfg],
            llm_cfg=self.llm_cfg.model_dump()
        )

# TODO: there should be a cachable interface
class InferenceResult(Serializable):
    def __init__(self, id: str, state: InferenceState, result: Optional[str]=None, error: Optional[str]=None):
        self.state = state
        self.result = result
        self.error = error    
        self.id = id  

    def __dict__(self) -> dict:
        return {
            "id": self.id,
            "state": self.state,
            "result": self.result,
            "error": self.error
        }

class TweetObject(Serializable):
    """Represents a tweet from Twitter."""

    def __init__(self, tweet_id, twitter_id, twitter_username, full_text, like_count=0, retweet_count=0, reply_count=0, impression_count=0, posted_at=None, **kwargs):
        """
        Initialize a new TweetObject.

        :param tweet_id: Unique identifier for the tweet.
        :param twitter_id: Unique identifier for the Twitter user.
        :param twitter_username: Username of the Twitter user.
        :param full_text: Full text of the tweet.
        :param like_count: Number of likes the tweet has received.
        :param retweet_count: Number of retweets the tweet has received.
        :param reply_count: Number of replies the tweet has received.
        :param impression_count: Number of times the tweet has been seen.
        :param posted_at: Timestamp of when the tweet was posted.
        """
        super().__init__()
        self.tweet_id = tweet_id
        self.twitter_id = twitter_id
        self.twitter_username = twitter_username
        self.like_count = like_count
        self.retweet_count = retweet_count
        self.reply_count = reply_count
        self.impression_count = impression_count
        self.full_text = full_text
        self.posted_at = posted_at

    def __dict__(self) -> dict:
        return {
            "tweet_id": self.tweet_id,
            "twitter_username": self.twitter_username,
            "impression_count": self.impression_count,
            "posted_at": self.posted_at,
            "reply_count": self.reply_count,
            "retweet_count": self.retweet_count,
            "like_count": self.like_count,
            "full_text": self.full_text
        }


class TwitterUserObject(Serializable):
    """Represents a Twitter user."""

    def __init__(self, twitter_id, twitter_username, name, followings_count = 0, followers_count = 0, is_blue_verified = False, followed=False, **kwargs):
        """
        Initialize a new TwitterUserObject.

        :param twitter_id: Unique identifier for the Twitter user.
        :param twitter_username: Username of the Twitter user.
        :param name: Display name of the Twitter user.
        :param followings_count: Number of users this user is following.
        :param followers_count: Number of followers this user has.
        :param is_blue_verified: Boolean indicating if the user is blue verified.
        :param followed: Boolean indicating if the user is followed by the current user.
        """
        super().__init__()
        self.twitter_id = twitter_id
        self.username = twitter_username
        self.name = name
        self.followings_count = followings_count
        self.followers_count = followers_count
        self.is_blue_verified = is_blue_verified
        self.followed = followed

    def __dict__(self) -> dict:
        return {
            "twitter_id": self.twitter_id,
            "username": self.username,
            "name": self.name,
            "followings_count": self.followings_count,
            "followers_count": self.followers_count,
            "is_blue_verified": self.is_blue_verified,
            "followed": self.followed
        }