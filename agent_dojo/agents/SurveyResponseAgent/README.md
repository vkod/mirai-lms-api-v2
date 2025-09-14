# Survey Response Agent

A DSPy-based agent that conducts surveys across multiple digital twin personas, collecting and consolidating their responses to provide market insights.

## Features

1. **Dynamic Survey Generation**: Automatically generates comprehensive survey questions from initial input
2. **Parallel Processing**: Surveys multiple personas simultaneously (5 at a time by default)
3. **Image-Based Surveys**: Can conduct surveys based on visual content (marketing materials, UI designs, etc.)
4. **Intelligent Consolidation**: Analyzes and consolidates responses to identify patterns and insights
5. **Persona Authenticity**: Each digital twin responds according to their unique characteristics and background

## How It Works

### 1. Survey Question Generation
- Takes initial survey questions or topics as input
- Expands them into a comprehensive set of 5-10 questions
- Handles both text-based and image-based surveys

### 2. Persona Selection
- Retrieves digital twins from Azure storage
- Can survey up to 20 personas by default (configurable)
- Optional: Target specific lead IDs for focused feedback

### 3. Parallel Response Collection
- Processes 5 personas simultaneously for efficiency
- Each persona responds authentically based on their profile
- Includes metadata (age, income, location, occupation) with responses

### 4. Response Consolidation
- Analyzes all responses to identify patterns
- Generates insights and key findings
- Provides both individual responses and aggregated analysis

## API Endpoints

### `/run_survey` - Text-Based Survey
```json
POST /run_survey
{
  "survey_input": "What features are most important in insurance products?",
  "is_image": false,
  "max_personas": 20,
  "lead_ids": null  // Optional: specific personas to survey
}
```

### `/run_image_survey` - Image-Based Survey
```json
POST /run_image_survey
{
  "image_base64": "base64_encoded_image_data",
  "initial_questions": "Is this design appealing? Would you click this button?",
  "max_personas": 15
}
```

## Response Format

```json
{
  "survey_questions": [
    "Question 1",
    "Question 2",
    ...
  ],
  "total_respondents": 15,
  "responses": [
    {
      "lead_id": "abc123",
      "classification": "hot",
      "responses": {
        "Question 1": "Answer from persona perspective",
        "Question 2": "Another answer"
      },
      "metadata": {
        "age": 35,
        "income": 120000,
        "location": "Sydney",
        "occupation": "Software Engineer"
      }
    },
    ...
  ],
  "consolidated_report": {
    "key_findings": "...",
    "patterns": [...],
    "insights": [...],
    "demographics": {...}
  },
  "summary": "Survey completed with 15 digital twin respondents. Key findings: ..."
}
```

## Use Cases

### Market Research
- Test product concepts with diverse personas
- Understand preferences across demographics
- Validate marketing messages

### UX Testing
- Get feedback on designs and interfaces
- Test user flows with different persona types
- Identify usability issues

### Campaign Testing
- Test marketing materials before launch
- Evaluate messaging effectiveness
- Optimize for different audience segments

### Product Development
- Gather feature requirements
- Prioritize development efforts
- Understand pain points

## Example Survey Questions

### Insurance Product Survey
```python
survey_input = """
1. What is your preferred method of receiving insurance information?
2. How important is online self-service for managing policies?
3. What factors are most important when choosing an insurance provider?
4. How comfortable are you with AI-assisted recommendations?
5. What additional services would you value?
"""
```

### Marketing Image Survey
```python
initial_questions = """
- Is the messaging clear and compelling?
- Does the visual design appeal to you?
- Would this motivate you to learn more?
- What improvements would you suggest?
"""
```

## Configuration

### Environment Variables
- `GROQ_LLAMA_MODEL`: Model for execution (default: 'openai/gpt-4-mini')
- `AZURE_STORAGE_CONNECTION_STRING`: For accessing digital twins
- `COSMOS_ENDPOINT` & `COSMOS_KEY`: For metadata queries

### Tuning Parameters
- `max_personas`: Maximum number of personas to survey (default: 20)
- `batch_size`: Number of parallel responses (default: 5)
- `temperature`: LLM temperature for response generation (default: 0.8)

## Optimization

The agent supports DSPy optimization but requires training data:

```python
# Future implementation
POST /optimize_survey_response_agent
```

Training data format would include:
- Sample surveys
- Expected persona responses
- Quality metrics for consolidation

## Best Practices

1. **Question Design**
   - Keep questions clear and specific
   - Avoid leading questions
   - Mix quantitative and qualitative questions

2. **Persona Selection**
   - Use diverse personas for broad insights
   - Target specific segments for focused feedback
   - Ensure adequate sample size (10-20 personas)

3. **Image Surveys**
   - Provide clear context for images
   - Include specific areas to evaluate
   - Keep image files reasonable in size

4. **Response Analysis**
   - Review both individual responses and patterns
   - Consider demographic factors in analysis
   - Use insights to inform decisions

## Limitations

- Requires digital twins to be present in storage
- Response quality depends on digital twin detail
- Processing time increases with persona count
- Image analysis is based on description, not visual AI

## Future Enhancements

- [ ] Support for multi-language surveys
- [ ] A/B testing capabilities
- [ ] Real-time streaming of responses
- [ ] Integration with analytics dashboards
- [ ] Custom persona filtering
- [ ] Response sentiment analysis
- [ ] Export to various formats (CSV, PDF)
- [ ] Scheduling and automation