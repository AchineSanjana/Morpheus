# Morpheus Sleep AI Assistant - Agent Roles & Communication Flow

Last Updated: October 21, 2025

Agents present in codebase: coordinator, coach, analyst, information, nutrition, addiction, storyteller, prediction. See `ARCHITECTURE_OVERVIEW.md` for system context.

## Overview

The Morpheus Sleep AI Assistant employs a sophisticated multi-agent architecture where specialized agents collaborate to provide comprehensive sleep coaching. This document defines the roles of each agent, their communication protocols, and the flow of information throughout the system.

## Agent Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                          AGENT ECOSYSTEM OVERVIEW                              │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                        COORDINATOR LAYER                                   │ │
│  │                                                                             │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────┐ │ │
│  │  │                      Coordinator Agent                                 │ │ │
│  │  │                                                                         │ │ │
│  │  │  Role: Master Orchestrator & Request Router                            │ │ │
│  │  │  ├── Intent Detection & Classification                                  │ │ │
│  │  │  ├── Agent Selection & Load Balancing                                  │ │ │
│  │  │  ├── Context Management & State Preservation                           │ │ │
│  │  │  ├── Response Aggregation & Synthesis                                  │ │ │
│  │  │  └── Error Handling & Fallback Management                              │ │ │
│  │  └─────────────────────────────────────────────────────────────────────────┘ │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                         │                                       │
│                            ┌─────────────┼─────────────┐                       │
│                            │             │             │                       │
│  ┌─────────────────────────────────────────────────────────────────────────────┐ │
│  │                       SPECIALIZED AGENT LAYER                              │ │
│  │                                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │ │
│  │  │   Coach     │  │  Analytics  │  │Information  │  │  Nutrition  │      │ │
│  │  │   Agent     │  │    Agent    │  │   Agent     │  │    Agent    │      │ │
│  │  │             │  │             │  │             │  │             │      │ │
│  │  │ Master      │  │ Data        │  │ Knowledge   │  │ Lifestyle   │      │ │
│  │  │ Sleep       │  │ Analysis    │  │ Provider    │  │ Optimizer   │      │ │
│  │  │ Coach       │  │ Specialist  │  │ & Educator  │  │ & Tracker   │      │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │ │
│  │                                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐      │ │
│  │  │  Addiction  │  │ Prediction  │  │ Storyteller │  │   Future    │      │ │
│  │  │    Agent    │  │    Agent    │  │    Agent    │  │   Agents    │      │ │
│  │  │             │  │             │  │             │  │             │      │ │
│  │  │ Behavioral  │  │ Sleep       │  │ Bedtime     │  │ • Medical   │      │ │
│  │  │ Change      │  │ Forecasting │  │ Stories &   │  │ • Therapy   │      │ │
│  │  │ Specialist  │  │ & Optimize  │  │ Audio Gen   │  │ • Community │      │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘      │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Agent Roles & Responsibilities

### 1. Coordinator Agent - The Master Orchestrator

#### Primary Role
The Coordinator Agent serves as the central intelligence hub, managing all user interactions and orchestrating communication between specialized agents.

#### Core Responsibilities

**Intent Detection & Classification**
```python
class CoordinatorAgent(BaseAgent):
    name = "coordinator"
    
    def __init__(self):
        super().__init__()
        self.action_type = "request_routing"
        
        # Intent classification patterns
        self.intent_patterns = {
            "analytics": ["analyze", "trend", "week", "report", "summary", "pattern"],
            "coach": ["plan", "tips", "improve", "advice", "coach", "help"],
            "information": ["what is", "explain", "tell me about", "define"],
            "nutrition": ["caffeine", "alcohol", "diet", "food", "eating", "exercise"],
            "addiction": ["quit", "craving", "dependence", "addicted", "stop"],
            "prediction": ["predict", "tonight", "tomorrow", "forecast", "bedtime", "optimal"],
            "storyteller": ["story", "tale", "bedtime", "read me"]
        }
    
    async def _detect_intent(self, message: str) -> str:
        """
        Multi-level intent detection:
        1. Keyword-based pattern matching
        2. LLM-powered semantic analysis
        3. Context-aware decision making
        """
```

**Agent Selection & Load Balancing**
- **Primary Agent Selection**: Routes to most appropriate specialist
- **Fallback Routing**: Secondary agent selection for complex queries
- **Load Distribution**: Balances requests across available agents
- **Context Preservation**: Maintains conversation state across agent switches

**Response Orchestration**
- **Multi-Agent Coordination**: Coordinates responses from multiple agents
- **Response Synthesis**: Combines insights from different specialists
- **Quality Assurance**: Ensures response coherence and completeness
- **Responsible AI Integration**: Applies ethical validation to all responses

#### Communication Interfaces

**Inbound Communications**
```python
# HTTP API Interface
@app.post("/chat")
async def chat_endpoint(request: ChatRequest, authorization: str = Header()):
    # Authentication & context setup
    user = await get_current_user(authorization)
    context = await build_agent_context(user, request)
    
    # Route to coordinator
    response = await coordinator.handle(request.message, context)
    
    # Apply responsible AI validation
    return await apply_responsible_ai_checks(response)
```

**Outbound Communications**
```python
# Agent Dispatch Protocol
async def dispatch_to_agent(self, agent_name: str, message: str, context: AgentContext):
    agent = self.agents[agent_name]
    
    # Pre-dispatch preparation
    enriched_context = await self.enrich_context(context, agent_name)
    
    # Execute agent handler
    response = await agent.handle(message, enriched_context)
    
    # Post-dispatch processing
    return await self.process_agent_response(response, agent_name)
```

### 2. Coach Agent - The Master Sleep Coach

#### Primary Role
The Coach Agent is the primary therapeutic interface, providing personalized sleep coaching based on Cognitive Behavioral Therapy for Insomnia (CBT-I) principles.

#### Core Specializations

**CBT-I Expertise**
```python
class CoachAgent(BaseAgent):
    name = "coach"
    
    def __init__(self):
        super().__init__()
        self.action_type = "sleep_coaching_plan"
        
        # Therapeutic frameworks
        self.coaching_frameworks = {
            "cbt_i": "Cognitive Behavioral Therapy for Insomnia",
            "sleep_hygiene": "Sleep Environment & Habits Optimization", 
            "circadian": "Circadian Rhythm Regulation",
            "stress_management": "Stress & Anxiety Reduction for Sleep"
        }
        
        # Responsible AI principles for inclusive coaching
        self.inclusive_coaching_principles = {
            "cultural_sensitivity": "Adapt to different cultural sleep practices",
            "accessibility": "Provide alternatives for different abilities",
            "economic_inclusivity": "Offer free and low-cost solutions",
            "age_inclusivity": "Tailor advice without stereotyping"
        }
```

**Personalized Plan Generation**
- **Individual Assessment**: Analyzes personal sleep patterns and challenges
- **Progressive Coaching**: Builds difficulty and complexity over time
- **Habit Tracking**: Monitors implementation of coaching recommendations
- **Adaptive Strategies**: Adjusts coaching based on user progress and feedback

**Safety & Crisis Management**
```python
# Safety screening patterns for urgent referrals
SAFETY_PATTERNS = {
    "sleep_apnea": ["stop breathing", "gasping", "choking", "snoring loudly"],
    "chronic_insomnia": ["can't sleep for weeks", "insomnia for months"],
    "medical_concerns": ["chest pain", "heart racing", "medication"],
    "urgent_symptoms": ["suicidal", "hallucinations", "microsleep driving"]
}

async def _detect_safety_concerns(self, message: str) -> List[str]:
    """Identifies when professional medical intervention is needed"""
```

#### Communication Protocols

**Data Requirements**
- **Sleep Logs**: Recent 7-14 days of sleep data for pattern analysis
- **User Profile**: Demographics and preferences for personalized coaching
- **Historical Progress**: Previous coaching outcomes and user feedback
- **Context Data**: Current life circumstances affecting sleep

**Response Format**
```python
# Structured coaching response
{
    "agent": "coach",
    "text": "Comprehensive coaching response with safety disclaimers",
    "data": {
        "safety_concerns": ["sleep_apnea", "chronic_insomnia"],
        "analysis": {
            "avg_duration": 6.2,
            "duration_trend": "improving",
            "problem_areas": ["bedtime_consistency", "screen_time"]
        },
        "plan": {
            "framework": "cbt_i_enhanced",
            "priority_actions": [...],
            "week_focus": "Bedtime consistency",
            "tracking_metrics": [...]
        },
        "responsible_ai_checks": {...}
    }
}
```

### 3. Analytics Agent - The Data Analysis Specialist

#### Primary Role
The Analytics Agent transforms raw sleep data into actionable insights through comprehensive pattern analysis and trend identification.

#### Core Capabilities

**Advanced Sleep Pattern Analysis**
```python
class AnalyticsAgent(BaseAgent):
    name = "analytics"
    
    def __init__(self):
        super().__init__()
        self.action_type = "data_analysis"
        
    async def _analyze_sleep_patterns(self, logs: List[Dict]) -> Dict[str, Any]:
        """
        Comprehensive analysis including:
        - Duration trends and sleep debt calculation
        - Bedtime/wake time consistency scoring
        - Sleep efficiency and quality patterns
        - Lifestyle factor correlation analysis
        - Weekly and monthly trend identification
        """
```

**Statistical Analysis & Insights**
- **Trend Detection**: Identifies improving, declining, or stable patterns
- **Correlation Analysis**: Links lifestyle factors to sleep quality
- **Comparative Analysis**: Benchmarks against healthy sleep ranges
- **Predictive Insights**: Forecasts potential sleep issues based on patterns

**Visual Data Preparation**
- **Chart Data Generation**: Prepares data for frontend visualization
- **Key Metrics Extraction**: Highlights most important findings
- **Progress Tracking**: Measures improvement over time
- **Goal Achievement**: Tracks progress toward sleep targets

#### Communication Protocols

**Input Data Processing**
```python
# Multi-source data integration
async def process_sleep_data(self, user_context: AgentContext) -> AnalysisResult:
    # Primary sleep logs
    logs = await fetch_recent_logs(user_id, days=30)
    
    # Lifestyle factor integration
    lifestyle_data = self.extract_lifestyle_factors(logs)
    
    # Historical trend analysis
    historical_trends = await self.analyze_historical_patterns(user_id)
    
    # Generate comprehensive analysis
    return self.synthesize_analysis(logs, lifestyle_data, historical_trends)
```

**Output Data Structure**
```python
{
    "agent": "analytics",
    "text": "Human-readable analysis summary",
    "data": {
        "analysis_period": "30 days",
        "total_nights": 28,
        "key_insights": [
            "Sleep duration improving by 0.5h/week",
            "Bedtime consistency needs improvement",
            "Weekend sleep pattern disruption identified"
        ],
        "metrics": {
            "avg_duration": 7.2,
            "sleep_efficiency": 85.4,
            "consistency_score": 72
        },
        "trends": {
            "duration": "improving",
            "quality": "stable", 
            "consistency": "declining"
        },
        "recommendations": [...]
    }
}
```

### 4. Information Agent - The Knowledge Provider & Educator

#### Primary Role
The Information Agent serves as the comprehensive knowledge base, providing evidence-based sleep science education and answering user questions.

#### Core Functions

**Sleep Science Education**
```python
class InformationAgent(BaseAgent):
    name = "information"
    
    def __init__(self):
        super().__init__()
        self.action_type = "general_response"
        
    async def _handle_core(self, message: str, ctx: AgentContext) -> AgentResponse:
        prompt = f"""
        You are a sleep science educator providing evidence-based information.
        
        Guidelines:
        - Use clear, accessible language
        - Cite current sleep research when relevant
        - Include practical applications
        - Always include medical disclaimer
        - Format for easy reading (bullets, sections)
        
        User question: "{message}"
        """
```

**Knowledge Domain Coverage**
- **Sleep Physiology**: How sleep works, sleep stages, circadian rhythms
- **Sleep Disorders**: Common issues like insomnia, sleep apnea, restless legs
- **Lifestyle Factors**: Impact of diet, exercise, environment, technology
- **Treatment Approaches**: CBT-I, sleep hygiene, medical interventions
- **Research Updates**: Latest findings in sleep science

**Educational Content Delivery**
- **Structured Responses**: Organized with clear sections and bullet points
- **Practical Applications**: Real-world implementation of sleep science
- **Evidence-Based Information**: Referenced to current research
- **Safety Disclaimers**: Clear medical advice boundaries

#### Communication Protocols

**Query Classification**
```python
def classify_information_request(self, message: str) -> str:
    """
    Categories:
    - physiological: How sleep works, brain activity, hormones
    - disorders: Sleep conditions and their symptoms
    - lifestyle: Diet, exercise, environment factors
    - treatment: Therapeutic approaches and interventions
    - research: Latest studies and findings
    """
```

**Response Formatting**
```python
{
    "agent": "information",
    "text": "Formatted educational content with disclaimer",
    "data": {
        "topic_category": "sleep_physiology",
        "key_concepts": ["REM sleep", "slow-wave sleep", "circadian rhythm"],
        "practical_applications": [...],
        "related_topics": [...],
        "sources": ["Sleep research citations"],
        "medical_disclaimer": "Educational purposes only - not medical advice"
    }
}
```

### 5. Nutrition Agent - The Lifestyle Optimizer & Tracker

#### Primary Role
The Nutrition Agent focuses on the intersection between lifestyle choices and sleep quality, providing guidance on diet, exercise, and daily habits.

#### Specialized Areas

**Nutritional Sleep Optimization**
```python
class NutritionAgent(BaseAgent):
    name = "nutrition"
    
    def __init__(self):
        super().__init__()
        self.action_type = "personalized_recommendation"
        
    async def analyze_lifestyle_patterns(self, logs: List[Dict]) -> LifestyleAnalysis:
        """
        Analyzes:
        - Caffeine consumption timing and frequency
        - Alcohol intake patterns and sleep impact
        - Exercise timing and intensity effects
        - Meal timing and composition influence
        - Screen time and blue light exposure
        """
```

**Pattern Recognition & Correlation**
- **Caffeine Impact Analysis**: Links late caffeine to sleep disruption
- **Alcohol Effect Tracking**: Monitors alcohol's impact on sleep quality
- **Exercise Optimization**: Recommends timing and intensity for better sleep
- **Dietary Sleep Support**: Suggests foods that promote better sleep

**Personalized Recommendations**
- **Individual Sensitivity**: Adapts to personal tolerance levels
- **Gradual Change Management**: Implements sustainable lifestyle modifications
- **Cultural Considerations**: Respects dietary restrictions and preferences
- **Budget-Conscious Options**: Provides accessible nutrition advice

#### Communication Protocols

**Lifestyle Data Integration**
```python
async def integrate_lifestyle_data(self, user_context: AgentContext) -> Dict:
    logs = user_context.get("logs", [])
    
    lifestyle_metrics = {
        "caffeine_nights": sum(1 for log in logs if log.get("caffeine_after3pm")),
        "alcohol_frequency": sum(1 for log in logs if log.get("alcohol")) / len(logs),
        "avg_screen_time": mean([log.get("screen_time_min", 0) for log in logs]),
        "exercise_patterns": self.analyze_exercise_patterns(logs)
    }
    
    return lifestyle_metrics
```

### 6. Addiction Agent - The Behavioral Change Specialist

#### Primary Role
The Addiction Agent provides specialized support for users dealing with substance dependencies that affect sleep, offering gentle guidance and professional referrals.

#### Core Competencies

**Addiction Detection & Assessment**
```python
class AddictionAgent(BaseAgent):
    name = "addiction"
    
    def __init__(self):
        super().__init__()
        self.action_type = "behavioral_change_suggestion"
        
        # Severity assessment patterns
        self.addiction_patterns = {
            "high_severity": ["can't stop", "withdrawal", "shaking", "panic without"],
            "medium_severity": ["addicted to", "dependent on", "crave", "multiple daily"],
            "low_severity": ["too much coffee", "habit", "routine"]
        }
```

**Supportive Intervention Strategies**
- **Harm Reduction**: Gradual reduction strategies rather than abrupt cessation
- **Professional Referrals**: Identifies when clinical intervention is needed
- **Motivational Support**: Encourages positive behavior change
- **Relapse Prevention**: Strategies for maintaining progress

**Sleep-Specific Focus**
- **Sleep-Disrupting Substances**: Caffeine, alcohol, nicotine, recreational drugs
- **Withdrawal Impact**: Managing sleep disruption during recovery
- **Replacement Behaviors**: Healthy alternatives to addictive substances
- **Support Resources**: Connects users with appropriate help

#### Communication Protocols

**Safety-First Approach**
```python
async def assess_intervention_level(self, message: str, severity: str) -> InterventionLevel:
    """
    Determines appropriate level of response:
    - EDUCATIONAL: Information and gentle suggestions
    - SUPPORTIVE: Structured reduction plans and encouragement  
    - REFERRAL: Professional treatment recommendations
    - CRISIS: Immediate professional intervention needed
    """
```

### 7. Prediction Agent - The Sleep Forecasting Specialist

#### Primary Role
The Prediction Agent provides AI-powered sleep quality forecasting and optimization recommendations based on daily activities, lifestyle factors, and historical sleep patterns.

#### Core Capabilities

**Sleep Quality Prediction**
```python
class SleepPredictionAgent(BaseAgent):
    name = "prediction"
    
    def __init__(self):
        super().__init__()
        self.action_type = "predictive_analysis"  # For responsible AI transparency
        
        # Prediction model weights
        self.prediction_models = {
            "sleep_quality": {
                "weights": {
                    "caffeine_after3pm": -1.2,
                    "alcohol": -0.8,
                    "screen_time": -0.01,  # per minute
                    "stress_level": -0.3,  # per point on 1-10 scale
                    "exercise_today": 0.5,
                    "consistency_bonus": 1.0,
                    "weekend_penalty": -0.3
                },
                "baseline": 7.0
            },
            "duration": {
                "weights": {
                    "caffeine_after3pm": -0.3,
                    "alcohol": -0.5,
                    "screen_time": -0.005,
                    "stress_level": -0.1,
                    "exercise_today": 0.2,
                    "age_factor": -0.02
                },
                "baseline": 7.5
            }
        }
    
    async def predict_sleep_quality(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predicts tonight's sleep quality (1-10 scale) based on:
        - Today's caffeine and alcohol consumption
        - Screen time before bed
        - Stress levels
        - Exercise activity
        - Historical sleep consistency
        """
```

**Optimal Bedtime Recommendations**
- **Circadian Rhythm Analysis**: Considers natural sleep-wake patterns
- **Sleep Debt Calculation**: Accounts for accumulated sleep deficit
- **Personal Schedule Integration**: Adapts to target wake times
- **Consistency Optimization**: Promotes regular sleep schedules
- **Timeline Generation**: Provides step-by-step preparation schedule

**Predictive Features**
```python
async def optimal_bedtime_recommendation(self, user_id: str, target_wake_time: str = "07:00") -> Dict:
    """
    Generates personalized bedtime recommendations including:
    - Optimal bedtime window for target wake time
    - Sleep preparation timeline (dinner, screen cutoff, wind-down, lights out)
    - Confidence score based on historical adherence
    - Alternative bedtimes if primary recommendation is impractical
    """
```

**AI-Enhanced Explanations**
- **Natural Language Insights**: Uses Gemini AI to explain predictions in user-friendly terms
- **Contextual Recommendations**: Provides actionable tips based on prediction factors
- **Encouraging Tone**: Maintains positive, motivational messaging
- **Scientific Grounding**: Balances accessibility with evidence-based reasoning

#### Communication Protocols

**Input Data Requirements**
```python
# User data for predictions
{
    "caffeine_after3pm": bool,
    "alcohol": bool,
    "screen_time_minutes": int,
    "stress_level": int (1-10),
    "exercise_today": bool,
    "recent_consistency": float (0-1),
    "age": int,
    "avg_duration": float,
    "recent_bedtimes": List[str]
}
```

**Prediction Response Format**
```python
{
    "agent": "prediction",
    "text": "AI-generated explanation of prediction",
    "data": {
        "prediction_type": "sleep_quality|optimal_bedtime",
        "predicted_quality": "Good|Fair|Poor",
        "quality_score": float (1-10),
        "predicted_duration": float (hours),
        "confidence": int (percentage),
        "key_factors": {
            "positive": List[str],  # Factors improving sleep
            "negative": List[str],  # Factors hindering sleep
            "neutral": List[str]    # Neutral factors
        },
        "recommendations": List[str],  # Actionable tips
        "optimal_bedtime": "HH:MM",    # If bedtime prediction
        "preparation_timeline": List[Dict],  # Step-by-step schedule
        "factors_analysis": str  # Detailed factor explanation
    }
}
```

**Integration with Other Agents**
- **Analytics Agent**: Receives historical pattern analysis for better predictions
- **Coach Agent**: Predictions inform coaching strategies and interventions
- **Nutrition Agent**: Lifestyle factors feed into prediction models
- **Coordinator**: Routes prediction requests based on keyword detection

### 8. Storyteller Agent - The Bedtime Story Creator

#### Primary Role
The Storyteller Agent generates calming, age-appropriate bedtime stories with comprehensive security validation and optional audio narration capabilities.

#### Core Capabilities

**Secure Story Generation**
```python
class StoryTellerAgent(BaseAgent):
    name = "storyteller"
    
    def __init__(self):
        super().__init__()
        self.action_type = "storytelling"  # For responsible AI context
        self.security_validator = SecurityValidator()
        self.audio_enabled = True
        self.recent_story_hashes = []  # Track recent stories to avoid repetition
        
    # Story themes with pre-validated elements
    STORY_THEMES = {
        "space": {
            "elements": ["stars", "planets", "moon", "galaxy", "cosmos"],
            "characters": ["astronaut", "friendly alien", "space explorer"],
            "settings": ["space station", "moon base", "starship"]
        },
        "nature": {
            "elements": ["forest", "meadow", "stream", "wildlife"],
            "characters": ["woodland creatures", "gentle animals"],
            "settings": ["peaceful forest", "flower garden", "quiet pond"]
        },
        # ... additional themes
    }
```

**Multi-Layered Security**
- **Input Sanitization**: Removes prompt injection patterns, SQL injection attempts, and malicious code
- **Output Validation**: Checks generated stories for age-inappropriate content, medical information, and PII
- **Fallback Stories**: Pre-validated safe stories used when AI generation fails or produces invalid content
- **Content Hashing**: Tracks recent stories to minimize repetition
- **User Name Protection**: Sanitizes and validates any user names included in stories

**Story Customization**
```python
# User preferences extraction
preferences = {
    "theme": "space|nature|ocean|fantasy|adventure",  # Pre-defined safe themes
    "length": "short|medium|long|extended",  # 120-2000 words
    "custom_topic": str,  # Sanitized custom topic (optional)
    "include_name": bool,  # Include user's name in story
    "mood": "calm"  # Always calm for bedtime
}

# Length options
STORY_LENGTHS = {
    "short": {"words": "120-180", "description": "A brief, gentle tale"},
    "medium": {"words": "800-1200", "description": "A comfortable bedtime story"},
    "long": {"words": "1200-1500", "description": "A longer, more detailed story"},
    "extended": {"words": "1500-2000", "description": "An immersive bedtime journey"}
}
```

**AI-Generated Content with Safety**
```python
async def _handle_core(self, message: str, ctx: Optional[AgentContext] = None) -> AgentResponse:
    # Step 1: Sanitize all user input
    sanitized_message = self.security_validator.sanitize_user_input(message)
    
    # Step 2: Extract preferences from sanitized input
    preferences = self._extract_story_preferences(sanitized_message, ctx)
    
    # Step 3: Build secure prompt with variation token for uniqueness
    prompt = self._build_enhanced_prompt(preferences, user_name, variation_token)
    
    # Step 4: Generate story with AI (with retry logic)
    for attempt in range(2):
        candidate_story = await generate_gemini_text(prompt)
        
        # Validate output for safety and appropriateness
        if self.security_validator.validate_story_output(candidate_story):
            # Check against recent stories to avoid repeats
            if not self._is_duplicate(candidate_story):
                story_text = candidate_story
                break
    
    # Step 5: Use fallback if AI generation fails
    if not story_text:
        story_text = self._select_fallback_story()
```

**Audio Generation Integration**
- **Optional Audio**: Users can request audio narration via button click (not automatic)
- **Audio Service**: Integrates with `audio_service.py` for text-to-speech generation
- **Caching**: Audio files cached for efficient delivery
- **Metadata**: Provides audio duration estimates and availability status

#### Communication Protocols

**Story Request Flow**
```
User Message → Input Sanitization → Preference Extraction → 
Prompt Building → AI Generation → Output Validation → 
Fallback (if needed) → Response Formatting → Audio Metadata Addition
```

**Response Format**
```python
{
    "agent": "storyteller",
    "text": "Story content (always provided as text first)",
    "data": {
        "preferences": {
            "theme": str,
            "length": str,
            "has_custom_topic": bool,
            "name_requested": bool
        },
        "generation_method": "ai_generated|fallback",
        "story_metadata": {
            "word_count": int,
            "character_count": int,
            "estimated_reading_time": str,
            "security_validated": bool,
            "content_hash": str  # For logging, not exposed to user
        },
        "audio_capability": {
            "available": bool,
            "can_generate": bool,
            "story_suitable_for_audio": bool,
            "estimated_audio_duration": str
        },
        "security_info": {
            "input_sanitized": bool,
            "output_validated": bool,
            "user_name_sanitized": bool,
            "prompt_secured": bool
        }
    }
}
```

**Security Validation Patterns**
```python
# Input sanitization removes:
- Prompt injection attempts ("ignore previous instructions", "system:", etc.)
- SQL injection patterns
- JavaScript code
- Python code execution attempts
- Special characters and excessive length

# Output validation blocks:
- Medical advice or health information
- Personal identifying information (emails, phone numbers, addresses)
- Age-inappropriate content (violence, scary themes, adult topics)
- Commercial or promotional content
- Real names of public figures
```

#### Integration Points
- **Audio Service**: Optional audio generation on user request
- **Coordinator**: Routes storytelling requests based on keywords like "story", "tale", "bedtime"
- **Responsible AI**: All stories pass through fairness and transparency checks
- **Security Middleware**: Additional layer of content validation

### 9. Future Agents (Planned)

The following agents are planned for future implementation:

**Medical Integration Agent**
- Professional medical record integration
- Sleep disorder screening
- Specialist referral management
- Medication interaction tracking

**Therapy Agent**
- CBT-I protocol implementation
- Progress tracking and homework
- Therapeutic intervention scheduling
- Mental health integration

**Community Agent**
- Peer support connections
- Group challenges and accountability
- Success story sharing
- Anonymous support forums

## Agent Communication Best Practices

### 1. Context Preservation
- Maintain conversation state across agent transitions
- Pass relevant historical data between agents
- Preserve user preferences and settings

### 2. Graceful Degradation
- Provide fallback responses when primary agent unavailable
- Route to secondary agents when primary agent confidence is low
- Use general responses when specialized knowledge not required

### 3. Responsible AI Integration
- All agent responses automatically validated
- Transparent explanation of AI decision-making
- User data protection at every stage
- Bias detection and mitigation

### 4. Performance Optimization
- Cache frequently requested analysis results
- Parallelize independent agent operations
- Implement smart request routing
- Monitor and optimize response times

## Conclusion

The Morpheus multi-agent architecture provides a sophisticated, scalable, and responsible approach to AI-powered sleep coaching. Each specialized agent contributes unique expertise while maintaining seamless coordination through the Coordinator Agent. The system prioritizes user safety, data privacy, and ethical AI practices at every level of communication.
- Token/length limits and calm tone guidance
- Pre-approved fallback stories when validation fails or LLM is unavailable

UX note: The app surfaces a privacy policy modal in both the main app and the auth screen, clarifying AI usage and data handling for story generation.

## Communication Flow Architecture

### Request Processing Flow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           COMMUNICATION FLOW DIAGRAM                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─────────────┐                                                               │
│  │ User Input  │                                                               │
│  │   Request   │                                                               │
│  └──────┬──────┘                                                               │
│         │                                                                      │
│         ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                    API Gateway Layer                                   │   │
│  │                                                                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │   │
│  │  │Authentication│  │Rate Limiting│  │   CORS      │                   │   │
│  │  │& Security   │  │& Throttling │  │ Handling    │                   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│         │                                                                      │
│         ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                  Coordinator Agent                                     │   │
│  │                                                                         │   │
│  │  ┌─────────────┐                                                       │   │
│  │  │   Intent    │ ──┐                                                   │   │
│  │  │ Detection   │   │                                                   │   │
│  │  └─────────────┘   │                                                   │   │
│  │                    │                                                   │   │
│  │  ┌─────────────┐   │  ┌─────────────┐                                 │   │
│  │  │   Context   │ ──┼──┤   Agent     │                                 │   │
│  │  │ Enrichment  │   │  │  Selection  │                                 │   │
│  │  └─────────────┘   │  └─────────────┘                                 │   │
│  │                    │                                                   │   │
│  │  ┌─────────────┐   │                                                   │   │
│  │  │ Load        │ ──┘                                                   │   │
│  │  │ Balancing   │                                                       │   │
│  │  └─────────────┘                                                       │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│         │                                                                      │
│         ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                 Agent Dispatch & Execution                             │   │
│  │                                                                         │   │
│  │  Analytics ◄──┐    Coach    ┌──► Information                           │   │
│  │   Agent       │    Agent    │     Agent                                │   │
│  │               │             │                                          │   │
│  │  Nutrition ◄──┼─────────────┼──► Addiction                            │   │
│  │   Agent       │             │     Agent                                │   │
│  │               │             │                                          │   │
│  │               └─────────────┘                                          │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│         │                                                                      │
│         ▼                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                 Response Processing                                    │   │
│  │                                                                         │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │   │
│  │  │ Response    │  │Responsible  │  │  Response   │                   │   │
│  │  │Aggregation  │  │AI Validation│  │ Enhancement │                   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
│         │                                                                      │
│         ▼                                                                      │
│  ┌─────────────┐                                                               │
│  │   Client    │                                                               │
│  │  Response   │                                                               │
│  └─────────────┘                                                               │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## API Communication Protocols

### REST API Interface

#### Standard Request Format
```python
POST /chat
Content-Type: application/json
Authorization: Bearer <jwt_token>

{
    "message": "I've been having trouble sleeping lately",
    "context": {
        "conversation_id": "uuid",
        "user_preferences": {...},
        "session_data": {...}
    }
}
```

#### Standard Response Format
```python
{
    "success": true,
    "timestamp": "2025-09-24T10:30:00Z",
    "response": {
        "agent": "coach",
        "text": "I understand you're having sleep difficulties...",
        "data": {
            "analysis": {...},
            "recommendations": [...],
            "next_steps": [...]
        },
        "responsible_ai_checks": {
            "fairness": {"passed": true, "risk_level": "low"},
            "transparency": {"passed": true, "risk_level": "low"},
            "ethical_data_handling": {"passed": true, "risk_level": "low"}
        }
    },
    "meta": {
        "processing_time": 1.25,
        "agent_chain": ["coordinator", "coach"],
        "context_used": ["sleep_logs", "user_profile"]
    }
}
```

### Inter-Agent Communication Protocol

#### Agent Context Object
```python
class AgentContext(Dict[str, Any]):
    """
    Standardized context passed between agents
    """
    # Required fields
    user: Dict[str, Any]          # User profile and authentication
    message: str                  # Original user message
    
    # Optional data fields
    logs: List[Dict]              # Recent sleep logs
    analysis: Dict[str, Any]      # Pre-computed analysis results
    conversation_history: List    # Previous interactions
    preferences: Dict             # User preferences and settings
    
    # System fields
    request_id: str               # Unique request identifier
    timestamp: datetime           # Request timestamp
    source_agent: str             # Originating agent
    processing_chain: List[str]   # Agent processing history
```

#### Agent Response Protocol
```python
class AgentResponse(TypedDict):
    """
    Standardized response format from all agents
    """
    agent: str                           # Agent identifier
    text: str                           # Human-readable response
    data: Dict[str, Any]                # Structured data payload
    
    # Responsible AI fields (automatically added by BaseAgent)
    responsible_ai_checks: Dict[str, Any]    # Validation results
    responsible_ai_passed: bool              # Overall validation status
    responsible_ai_risk_level: str           # Risk assessment
    
    # Optional fields
    confidence: float                    # Response confidence (0-1)
    requires_followup: bool             # Needs additional interaction
    referral_needed: bool               # Professional referral required
    data_sources: List[str]             # Data sources used
    processing_time: float              # Response generation time
```

### MCP (Model Context Protocol) Integration

#### Future MCP Implementation
```python
class MorpheusMCPServer:
    """
    Model Context Protocol server for advanced AI integration
    """
    
    def __init__(self):
        self.agents = {
            'coordinator': CoordinatorAgent(),
            'coach': CoachAgent(),
            'analytics': AnalyticsAgent(),
            'information': InformationAgent(),
            'nutrition': NutritionAgent(),
            'addiction': AddictionAgent()
        }
    
    async def handle_mcp_request(self, request: MCPRequest) -> MCPResponse:
        """
        Process MCP requests with enhanced context and multi-agent coordination
        """
        # Extract context from MCP request
        context = self.extract_mcp_context(request)
        
        # Route through coordinator
        response = await self.agents['coordinator'].handle(
            request.message, 
            context
        )
        
        # Format as MCP response
        return self.format_mcp_response(response)
    
    def extract_mcp_context(self, request: MCPRequest) -> AgentContext:
        """
        Convert MCP context to internal agent context format
        """
        return AgentContext({
            'user': request.user_context,
            'message': request.content,
            'tools_available': request.available_tools,
            'model_context': request.model_context,
            'session_data': request.session_data
        })
```

## Communication Patterns

### 1. Direct Agent Communication

**Single Agent Response**
```
User → Coordinator → Coach Agent → Response
```

**Use Cases:**
- Simple coaching questions
- General information requests
- Direct nutritional advice

### 2. Multi-Agent Coordination

**Sequential Processing**
```
User → Coordinator → Analytics Agent → Coach Agent → Response
```

**Parallel Processing**
```
User → Coordinator → ┌── Analytics Agent ──┐
                     ├── Nutrition Agent ──┤ → Synthesis → Response
                     └── Information Ag. ──┘
```

**Use Cases:**
- Complex sleep analysis requiring multiple perspectives
- Comprehensive coaching plans
- Multi-factor lifestyle recommendations

### 3. Escalation Patterns

**Professional Referral Chain**
```
User → Coach Agent → [Safety Concern Detected] → Addiction Agent → [High Risk] → Professional Referral
```

**Medical Emergency Protocol**
```
Any Agent → [Critical Symptoms] → Immediate Safety Response → Emergency Resources
```

## Error Handling & Fallback Protocols

### Agent Failure Management

```python
class AgentFailureHandler:
    async def handle_agent_failure(self, agent_name: str, error: Exception, context: AgentContext):
        """
        Multi-level fallback strategy:
        1. Retry with exponential backoff
        2. Route to backup agent
        3. Provide generic response
        4. Escalate to human support
        """
        
        # Level 1: Retry with backoff
        if self.should_retry(error):
            return await self.retry_with_backoff(agent_name, context)
        
        # Level 2: Backup agent routing
        backup_agent = self.get_backup_agent(agent_name)
        if backup_agent:
            return await backup_agent.handle(context.message, context)
        
        # Level 3: Generic response
        return self.generate_fallback_response(agent_name, error)
        
        # Level 4: Human escalation (if critical)
        if self.is_critical_failure(error):
            await self.escalate_to_human_support(context, error)
```

### Communication Timeout Handling

```python
# Timeout configurations by operation type
TIMEOUT_CONFIG = {
    "intent_detection": 2.0,      # Quick intent classification
    "simple_response": 5.0,       # Basic agent responses
    "complex_analysis": 15.0,     # Deep sleep analysis
    "multi_agent": 20.0,          # Multi-agent coordination
    "llm_generation": 30.0        # LLM text generation
}
```

## Performance Optimization

### Caching Strategies

**Response Caching**
```python
@cache(ttl=3600)  # 1 hour cache
async def get_information_response(query_hash: str, user_context_hash: str):
    """Cache information agent responses for common queries"""
    
@cache(ttl=1800)  # 30 minute cache
async def get_analysis_results(user_id: str, data_hash: str):
    """Cache analytics results for unchanged data"""
```

**Context Caching**
```python
@cache(ttl=300)   # 5 minute cache
async def get_user_context(user_id: str):
    """Cache user context data for active sessions"""
```

### Load Balancing

**Agent Instance Management**
```python
class AgentLoadBalancer:
    def __init__(self):
        self.agent_pools = {
            'coach': [CoachAgent() for _ in range(3)],
            'analytics': [AnalyticsAgent() for _ in range(2)],
            'information': [InformationAgent() for _ in range(2)]
        }
    
    async def get_available_agent(self, agent_type: str) -> BaseAgent:
        """Round-robin selection of available agent instances"""
        pool = self.agent_pools[agent_type]
        return min(pool, key=lambda agent: agent.current_load)
```

## Monitoring & Observability

### Communication Metrics

```python
# Key metrics tracked
COMMUNICATION_METRICS = {
    "request_routing_time": "Time to route request to appropriate agent",
    "agent_response_time": "Individual agent processing time", 
    "inter_agent_latency": "Communication delay between agents",
    "context_preparation_time": "Time to prepare agent context",
    "response_synthesis_time": "Time to combine multi-agent responses",
    "responsible_ai_validation_time": "Time for ethical validation",
    "total_request_time": "End-to-end request processing time"
}
```

### Health Monitoring

```python
@app.get("/health/agents")
async def agent_health_check():
    """Check health of all agents and communication channels"""
    health_status = {}
    
    for agent_name, agent in agents.items():
        try:
            # Test basic agent functionality
            test_response = await agent.handle("health check", minimal_context)
            health_status[agent_name] = {
                "status": "healthy",
                "response_time": test_response.processing_time,
                "last_check": datetime.now().isoformat()
            }
        except Exception as e:
            health_status[agent_name] = {
                "status": "unhealthy",
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
    
    return health_status
```

## Security Considerations

### Agent Authentication

```python
class AgentSecurityManager:
    def __init__(self):
        self.agent_credentials = {
            agent_name: self.generate_agent_token(agent_name)
            for agent_name in ['coordinator', 'coach', 'analytics', 'information', 'nutrition', 'addiction']
        }
    
    async def authenticate_agent_communication(self, source_agent: str, target_agent: str, context: AgentContext):
        """Verify legitimate inter-agent communication"""
        # Validate agent tokens
        # Check communication permissions
        # Audit communication attempts
```

### Data Flow Security

**Context Sanitization**
```python
async def sanitize_agent_context(context: AgentContext, target_agent: str) -> AgentContext:
    """
    Remove sensitive data not needed by target agent:
    - PII not relevant to agent function
    - Excessive historical data
    - System internal information
    """
```

**Response Validation**
```python
async def validate_agent_response(response: AgentResponse) -> AgentResponse:
    """
    Security validation before sending response:
    - Check for data leakage
    - Validate responsible AI compliance
    - Ensure appropriate content filtering
    """
```

## Future Enhancements

### Advanced Communication Patterns

**1. Agent Collaboration Networks**
- **Peer-to-Peer Learning**: Agents share insights to improve recommendations
- **Consensus Building**: Multiple agents collaborate on complex cases
- **Specialization Evolution**: Agents develop deeper expertise in sub-domains

**2. Real-Time Communication**
- **WebSocket Integration**: Live agent-to-agent communication
- **Event-Driven Architecture**: Reactive agent responses to data changes
- **Stream Processing**: Continuous analysis and coaching adjustments

**3. AI-Enhanced Routing**
- **Machine Learning Intent Detection**: Improved request classification
- **Dynamic Agent Selection**: AI-optimized agent routing based on success patterns
- **Contextual Understanding**: Deeper comprehension of user needs and preferences

### Integration Expansions

**1. External System Integration**
- **Health App APIs**: Integration with fitness trackers and health platforms
- **Telemedicine Platforms**: Connection with healthcare provider systems
- **Research Databases**: Access to latest sleep science research

**2. Multi-Modal Communication**
- **Voice Interface**: Spoken interactions with sleep coaches
- **Visual Analysis**: Image-based sleep environment assessment
- **Biometric Integration**: Real-time physiological data incorporation

## Conclusion

The Morpheus Sleep AI Assistant's agent architecture represents a sophisticated, scalable, and ethically-designed communication system. The clear role definitions, robust communication protocols, and comprehensive error handling ensure reliable, effective sleep coaching while maintaining the highest standards of responsible AI.

Key architectural strengths:
- **Clear Role Separation**: Each agent has distinct expertise and responsibilities
- **Robust Communication**: Well-defined protocols ensure reliable inter-agent communication
- **Scalable Design**: Architecture supports growth and enhanced functionality
- **Responsible AI Integration**: Ethical considerations built into every communication layer
- **User-Centric Approach**: All communication optimized for user benefit and safety
- **Professional Integration**: Clear pathways for clinical referrals when needed

This communication architecture serves as a model for multi-agent AI systems in healthcare, demonstrating how specialized AI agents can work together to provide comprehensive, ethical, and effective user support.

---

*Document Version: 1.0.0*
*Last Updated: September 24, 2025*
*Communication Protocol Review: Monthly*