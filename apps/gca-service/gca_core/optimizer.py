"""
GCA Optimizer: Intent Routing and Geometric Navigation
Routes user intents to appropriate skill vectors and manages cognitive flow.
"""

import torch
from typing import Optional, Dict, List
import logging
from .tools import ToolRegistry, Tool

logger = logging.getLogger("GCA.Optimizer")


class GCAOptimizer:
    """
    The Optimizer routes user intents through geometric space.
    It determines which skill vectors to apply for a given task.
    """
    
    def __init__(self, glassbox, memory):
        """
        Initialize the optimizer.
        
        Args:
            glassbox: GlassBox instance for activation analysis
            memory: IsotropicMemory instance for vector retrieval
        """
        self.glassbox = glassbox
        self.memory = memory
        self.intent_cache = {}
        self.tool_registry = ToolRegistry()
        logger.info("GCA Optimizer initialized")
        
    def select_relevant_tools(self, user_input: str, available_tool_names: List[str]) -> List[Tool]:
        """
        Select relevant tools based on user input and intent.
        Prioritizes tools that match the detected intent vector.
        """
        intent = self.route_intent(user_input)
        relevant_tools = []

        for name in available_tool_names:
            tool = self.tool_registry.get(name)
            if not tool:
                # If tool is not in registry, create a generic one so we don't drop it
                tool = Tool(name=name, description="External tool", parameters={}, intent_vector="GENERAL")

            # Weigh GCA components heavily:
            # If the tool's intent vector matches the routed intent, it's highly relevant.
            if tool.intent_vector == intent:
                relevant_tools.insert(0, tool) # Prioritize
            elif tool.intent_vector == "GENERAL":
                relevant_tools.append(tool)
            else:
                relevant_tools.append(tool)

        return relevant_tools

    def prioritize_tools(self, tools: List[Tool], user_input: str) -> List[Tool]:
        """
        Prioritize a list of Tool objects based on user intent.
        Similar to select_relevant_tools but accepts objects instead of names.

        Args:
            tools: List of Tool objects
            user_input: User intent/input string

        Returns:
            Sorted list of Tool objects
        """
        intent = self.route_intent(user_input)
        prioritized = []
        general = []
        others = []

        for tool in tools:
            # Check if tool intent matches
            # Some tools might not have intent_vector attribute if dynamically created without it
            # But the Tool class has it.
            tool_intent = getattr(tool, 'intent_vector', "GENERAL")

            if tool_intent == intent:
                prioritized.append(tool)
            elif tool_intent == "GENERAL":
                general.append(tool)
            else:
                others.append(tool)

        # Combine: Prioritized > General > Others
        return prioritized + general + others

    def route_intent(self, user_input: str) -> str:
        """
        Analyze user input and route to appropriate skill vector.
        
        Args:
            user_input: Raw user input text
            
        Returns:
            Name of the most appropriate skill vector
        """
        # Check cache
        if user_input in self.intent_cache:
            return self.intent_cache[user_input]
            
        # Extract activation for the input
        activation = self.glassbox.get_activation(user_input)
        
        # Find most similar skill vector
        similar = self.memory.find_similar(activation, top_k=1)
        
        if similar:
            intent = similar[0][0]
            logger.info(f"Routed intent: '{user_input[:50]}...' -> {intent}")
            self.intent_cache[user_input] = intent
            return intent
        else:
            # Default to a general skill
            default_intent = "GENERAL"
            logger.warning(f"No matching intent found, using default: {default_intent}")
            return default_intent
            
    def classify_intent_type(self, user_input: str) -> Dict[str, float]:
        """
        Classify the type of intent (question, command, conversation, etc.).
        
        Args:
            user_input: User input text
            
        Returns:
            Dictionary of intent types with confidence scores
        """
        # Simple keyword-based classification (can be enhanced with ML)
        intent_types = {
            "question": 0.0,
            "command": 0.0,
            "conversation": 0.0,
            "creative": 0.0,
            "analytical": 0.0
        }
        
        lower_input = user_input.lower()
        
        # Question indicators
        if any(word in lower_input for word in ["what", "why", "how", "when", "where", "who", "?"]):
            intent_types["question"] = 0.8
            
        # Command indicators
        if any(word in lower_input for word in ["create", "delete", "send", "run", "execute", "build"]):
            intent_types["command"] = 0.7
            
        # Conversation indicators
        if any(word in lower_input for word in ["hello", "hi", "thanks", "please", "sorry"]):
            intent_types["conversation"] = 0.6
            
        # Creative indicators
        if any(word in lower_input for word in ["write", "design", "imagine", "create", "generate"]):
            intent_types["creative"] = 0.7
            
        # Analytical indicators
        if any(word in lower_input for word in ["analyze", "calculate", "compare", "evaluate", "assess"]):
            intent_types["analytical"] = 0.8
            
        # Normalize
        total = sum(intent_types.values())
        if total > 0:
            intent_types = {k: v/total for k, v in intent_types.items()}
            
        return intent_types
        
    def select_steering_strategy(
        self,
        user_input: str,
        available_skills: List[str]
    ) -> Dict[str, float]:
        """
        Select which skill vectors to apply and with what strength.
        
        Args:
            user_input: User input text
            available_skills: List of available skill vector names
            
        Returns:
            Dictionary mapping skill names to steering strengths
        """
        intent_types = self.classify_intent_type(user_input)
        strategy = {}
        
        # Map intent types to skills
        skill_mapping = {
            "question": ["LOGIC", "KNOWLEDGE", "CLARITY"],
            "command": ["EXECUTION", "PRECISION", "SAFETY"],
            "conversation": ["EMPATHY", "WARMTH", "HUMOR"],
            "creative": ["CREATIVITY", "IMAGINATION", "ORIGINALITY"],
            "analytical": ["LOGIC", "ANALYSIS", "RIGOR"]
        }
        
        for intent_type, confidence in intent_types.items():
            if confidence > 0.3:  # Threshold for consideration
                recommended_skills = skill_mapping.get(intent_type, [])
                for skill in recommended_skills:
                    if skill in available_skills:
                        # Accumulate strength
                        strategy[skill] = strategy.get(skill, 0.0) + confidence
                        
        # Normalize strengths to reasonable range (0.5 to 2.0)
        if strategy:
            max_strength = max(strategy.values())
            strategy = {
                k: 0.5 + (v / max_strength) * 1.5
                for k, v in strategy.items()
            }
            
        logger.debug(f"Steering strategy: {strategy}")
        return strategy
        
    def optimize_path(
        self,
        start_state: str,
        goal_state: str,
        constraints: Optional[List[str]] = None
    ) -> List[str]:
        """
        Find optimal path through skill space from start to goal.
        
        Args:
            start_state: Starting state description
            goal_state: Desired end state description
            constraints: Optional list of constraints
            
        Returns:
            List of skill vectors to apply in sequence
        """
        # Simplified path finding (can be enhanced with A* or similar)
        start_vec = self.glassbox.get_activation(start_state)
        goal_vec = self.glassbox.get_activation(goal_state)
        
        # Find intermediate skills that bridge the gap
        available_skills = self.memory.list_vectors()
        path = []
        
        current_vec = start_vec
        max_steps = 5
        
        for step in range(max_steps):
            # Find skill that moves us closest to goal
            best_skill = None
            best_distance = float('inf')
            
            for skill_name in available_skills:
                skill_vec = self.memory.get_vector(skill_name)
                if skill_vec is None:
                    continue
                    
                # Simulate applying this skill
                next_vec = current_vec + skill_vec * 0.5
                distance = torch.norm(next_vec - goal_vec).item()
                
                if distance < best_distance:
                    best_distance = distance
                    best_skill = skill_name
                    
            if best_skill:
                path.append(best_skill)
                skill_vec = self.memory.get_vector(best_skill)
                current_vec = current_vec + skill_vec * 0.5
                
                # Check if we've reached the goal
                if best_distance < 0.1:
                    break
            else:
                break
                
        logger.info(f"Optimized path: {' -> '.join(path)}")
        return path
