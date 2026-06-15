/**
 * ResponseFormatter Component
 * Formats different types of orchestrator responses with proper styling
 */

import {
  ClipboardList,
  Package,
  List,
  BookOpen,
  Lightbulb,
  CheckCircle,
  Sparkles,
  Presentation,
  AlertTriangle,
  HelpCircle,
  Heart,
  Rocket,
  Target,
  Flower2,
  RotateCcw,
  Info,
  Zap,
  Handshake,
  ShieldCheck,
  Video,
  Globe,
  FileText,
  ExternalLink,
  Check,
  Search,
  MessageCircle,
  ThumbsUp,
  ThumbsDown,
} from "lucide-react";

// Utility function to parse text with bold formatting (**text**) - exported for use in Discuss, etc.
export const parseBoldText = (text) => {
  if (!text) return text;

  const parts = [];
  let lastIndex = 0;
  const regex = /\*\*(.*?)\*\*/g;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }
    parts.push(<strong key={match.index} className="font-bold">{match[1]}</strong>);
    lastIndex = regex.lastIndex;
  }

  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 0 ? parts : text;
};

/**
 * Quick Answer Response
 * For simple calculations, facts, and short queries
 */
const QuickAnswerResponse = ({ data }) => {
  const answer = data.answer || "";

  return (
    <div className="space-y-4">
      <div
        className="border-2 border-[#000000] p-6 rounded-lg shadow-[3px_3px_0px_0px_#000000]"
        style={{ backgroundColor: "#A7F3D0" }}
      >
        <div className="flex items-start gap-3">
          <div className="mt-1">
            <Zap size={24} className="text-[#000000]" />
          </div>
          <div className="flex-1">
            <div className="text-xs font-bold text-[#000000] opacity-70 uppercase tracking-wide mb-2">
              Quick Answer
            </div>
            <p className="text-2xl font-bold text-[#000000] leading-relaxed">
              {parseBoldText(answer)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * General Conversation Response
 * For greetings, gratitude, clarifications, and out-of-scope queries
 */
const GeneralConversationResponse = ({ data }) => {
  const responseType = data.response_type || "general";
  const response = data.response || "";
  const suggestedTopics = data.suggested_topics || [];

  // Icons for different response types
  const icons = {
    greeting: <Handshake size={20} className="text-[#000000]" />,
    gratitude: <Heart size={20} className="text-[#000000]" />,
    clarification: <HelpCircle size={20} className="text-[#000000]" />,
    out_of_scope: <Info size={20} className="text-[#000000]" />,
    unclear: <AlertTriangle size={20} className="text-[#000000]" />,
    general: <Sparkles size={20} className="text-[#000000]" />,
  };

  const colors = {
    greeting: "#D4F1C5",
    gratitude: "#FFB7C5",
    clarification: "#FDE047",
    out_of_scope: "#E0EEEF",
    unclear: "#FFE4B5",
    general: "#E8D5FF",
  };

  const bgColor = colors[responseType] || colors.general;
  const icon = icons[responseType] || icons.general;

  return (
    <div className="space-y-4">
      <div
        className="border-2 border-[#000000] p-5 rounded-lg shadow-[3px_3px_0px_0px_#000000]"
        style={{ backgroundColor: bgColor }}
      >
        <div className="flex items-start gap-3">
          <div className="mt-1">{icon}</div>
          <p className="text-base text-[#000000] leading-relaxed flex-1">
            {parseBoldText(response)}
          </p>
        </div>

        {suggestedTopics.length > 0 && (
          <div className="mt-4 pt-4 border-t-2 border-[#000000]">
            <p className="text-sm font-bold text-[#000000] mb-2">
              I can help you with:
            </p>
            <div className="flex flex-wrap gap-2">
              {suggestedTopics.map((topic, idx) => (
                <span
                  key={idx}
                  className="bg-white border-2 border-[#000000] px-3 py-1 rounded-full text-xs font-medium text-[#000000] shadow-[2px_2px_0px_0px_#000000]"
                >
                  {topic}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

const ActivityResponse = ({ data }) => (
  <div className="space-y-4">
    <div className="bg-[#EDF4EC] border-2 border-[#000000] p-4 rounded-lg">
      <h3 className="text-xl font-bold text-[#000000] mb-2 flex items-center gap-2">
        <ClipboardList size={18} /> {data.activity_name}
      </h3>
      <p className="text-sm text-[#000000]">{parseBoldText(data.description)}</p>
      <div className="mt-2 flex items-center gap-2 text-xs text-[#000000]">
        <span className="bg-white border border-[#000000] px-2 py-1 rounded">
          Duration: {data.duration_minutes} minutes
        </span>
      </div>
    </div>

    <div className="bg-[#feffdf] border-2 border-[#000000] p-4 rounded-lg">
      <h4 className="font-bold text-[#000000] mb-2 flex items-center gap-2">
        <Package size={18} /> Materials Needed
      </h4>
      <ul className="space-y-1 text-sm">
        {data.materials_needed?.map((item, idx) => (
          <li key={idx} className="flex items-start gap-2">
            <span className="text-[#000000]">•</span>
            <span className="text-[#000000]">{parseBoldText(item)}</span>
          </li>
        ))}
      </ul>
    </div>

    <div className="bg-[#ffefed] border-2 border-[#000000] p-4 rounded-lg">
      <h4 className="font-bold text-[#000000] mb-3 flex items-center gap-2">
        <List size={18} /> Steps
      </h4>
      <div className="space-y-3">
        {data.steps?.map((step, idx) => (
          <div key={idx} className="flex gap-3 bg-white border-2 border-[#000000] p-3 rounded">
            <span className="flex-shrink-0 w-6 h-6 bg-[#D4F1C5] border-2 border-[#000000] rounded-full flex items-center justify-center text-xs font-bold">
              {idx + 1}
            </span>
            <span className="text-sm text-[#000000] flex-1 pt-0.5">{parseBoldText(step)}</span>
          </div>
        ))}
      </div>
    </div>

    <div className="bg-[#FDE047] border-2 border-[#000000] p-5 rounded-lg shadow-[3px_3px_0px_0px_#000000]">
      <h4 className="font-bold text-[#000000] mb-2 flex items-center gap-2">
        <BookOpen size={18} /> Learning Outcome
      </h4>
      <p className="text-sm text-[#000000]">{parseBoldText(data.learning_outcome)}</p>
    </div>

    {data.tips && data.tips.length > 0 && (
      <div className="bg-gradient-to-r from-[#E8D5FF] to-[#DDD6FE] border-2 border-[#000000] p-5 rounded-lg shadow-[3px_3px_0px_0px_#000000]">
        <h4 className="font-bold text-[#000000] mb-2 flex items-center gap-2">
          <Lightbulb size={18} /> Tips
        </h4>
        <ul className="space-y-2 text-sm">
          {data.tips.map((tip, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <span className="text-[#000000]">•</span>
              <span className="text-[#000000]">{parseBoldText(tip)}</span>
            </li>
          ))}
        </ul>
      </div>
    )}
  </div>
);

const ExpertTeacherResponse = ({ data }) => (
  <div className="space-y-4">
    <div className="bg-white border-2 border-[#000000] p-4 rounded-lg">
      <p className="text-sm text-[#000000] leading-relaxed whitespace-pre-wrap">
        {parseBoldText(data.explanation)}
      </p>
    </div>

    {data.key_points && data.key_points.length > 0 && (
      <div className="bg-[#EDF4EC] border-2 border-[#000000] p-4 rounded-lg">
        <h4 className="font-bold text-[#000000] mb-2 flex items-center gap-2">
          <CheckCircle size={18} /> Key Points
        </h4>
        <ul className="space-y-2 text-sm">
          {data.key_points.map((point, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <span className="text-[#000000]">•</span>
              <span className="text-[#000000]">{parseBoldText(point)}</span>
            </li>
          ))}
        </ul>
      </div>
    )}

    {data.examples && data.examples.length > 0 && (
      <div className="bg-[#D4F1C5] border-2 border-[#000000] p-4 rounded-lg">
        <h4 className="font-bold text-[#000000] mb-2 flex items-center gap-2">
          <Sparkles size={18} /> Examples
        </h4>
        <ul className="space-y-2 text-sm">
          {data.examples.map((example, idx) => (
            <li key={idx} className="text-[#000000]">
              {example}
            </li>
          ))}
        </ul>
      </div>
    )}

    {data.teaching_tips && data.teaching_tips.length > 0 && (
      <div className="bg-[#E8D5FF] border-2 border-[#000000] p-4 rounded-lg">
        <h4 className="font-bold text-[#000000] mb-2 flex items-center gap-2">
          <Presentation size={18} /> Teaching Tips
        </h4>
        <ul className="space-y-2 text-sm">
          {data.teaching_tips.map((tip, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <span className="text-[#000000]">•</span>
              <span className="text-[#000000]">{parseBoldText(tip)}</span>
            </li>
          ))}
        </ul>
      </div>
    )}

    {data.common_misconceptions && data.common_misconceptions.length > 0 && (
      <div className="bg-[#F99DA8] border-2 border-[#000000] p-4 rounded-lg">
        <h4 className="font-bold text-[#000000] mb-2 flex items-center gap-2">
          <AlertTriangle size={18} /> Common Misconceptions
        </h4>
        <ul className="space-y-2 text-sm">
          {data.common_misconceptions.map((misconception, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <span className="text-[#000000]">•</span>
              <span className="text-[#000000]">{parseBoldText(misconception)}</span>
            </li>
          ))}
        </ul>
      </div>
    )}

    {data.follow_up_questions && data.follow_up_questions.length > 0 && (
      <div className="bg-[#E0EEEF] border-2 border-[#000000] p-4 rounded-lg">
        <h4 className="font-bold text-[#000000] mb-2 flex items-center gap-2">
          <HelpCircle size={18} /> Follow-up Questions
        </h4>
        <ul className="space-y-2 text-sm">
          {data.follow_up_questions.map((question, idx) => (
            <li key={idx} className="text-[#000000]">
              {question}
            </li>
          ))}
        </ul>
      </div>
    )}
  </div>
);

const ContentExplanationResponse = ({ data }) => (
  <div className="space-y-4">
    <div className="bg-white border-2 border-[#000000] p-4 rounded-lg">
      <p className="text-sm text-[#000000] leading-relaxed whitespace-pre-wrap">
        {parseBoldText(data.explanation)}
      </p>
    </div>

    {data.key_points && data.key_points.length > 0 && (
      <div className="bg-[#EDF4EC] border-2 border-[#000000] p-4 rounded-lg">
        <h4 className="font-bold text-[#000000] mb-2 flex items-center gap-2">
          <CheckCircle size={18} /> Key Points
        </h4>
        <ul className="space-y-2 text-sm">
          {data.key_points.map((point, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <span className="text-[#000000]">•</span>
              <span className="text-[#000000]">{parseBoldText(point)}</span>
            </li>
          ))}
        </ul>
      </div>
    )}

    {data.examples && data.examples.length > 0 && (
      <div className="bg-[#D4F1C5] border-2 border-[#000000] p-4 rounded-lg">
        <h4 className="font-bold text-[#000000] mb-2 flex items-center gap-2">
          <Sparkles size={18} /> Examples
        </h4>
        <ul className="space-y-2 text-sm">
          {data.examples.map((example, idx) => (
            <li key={idx} className="text-[#000000]">
              {parseBoldText(example)}
            </li>
          ))}
        </ul>
      </div>
    )}

    {data.sources && data.sources.length > 0 && (
      <div className="bg-[#E0EEEF] border-2 border-[#000000] p-4 rounded-lg">
        <h4 className="font-bold text-[#000000] mb-2 flex items-center gap-2 text-xs">
          <BookOpen size={18} /> NCERT Sources
        </h4>
        <div className="flex flex-wrap gap-2">
          {data.sources.map((source, idx) => (
            <span
              key={idx}
              className="text-xs bg-white border border-[#000000] px-2 py-1 rounded"
            >
              {source}
            </span>
          ))}
        </div>
      </div>
    )}
  </div>
);

/**
 * Renders plain text with paragraphs and simple lists (• or 1. 2.) for readable structure
 */
const DefaultResponse = ({ text }) => {
  if (!text) return null;
  const trimmed = String(text).trim();
  if (!trimmed) return null;

  const lines = trimmed.split(/\n/);
  const blocks = [];
  let i = 0;
  const blockClass = "text-sm md:text-base leading-relaxed";

  while (i < lines.length) {
    const line = lines[i];
    const trimmedLine = line.trim();
    if (!trimmedLine) {
      i++;
      continue;
    }
    // Numbered list (1. 2. or 1) 2))
    if (/^\d+[.)]\s/.test(trimmedLine)) {
      const listItems = [];
      while (i < lines.length && /^\d+[.)]\s/.test(lines[i].trim())) {
        listItems.push(lines[i].trim().replace(/^\d+[.)]\s*/, ""));
        i++;
      }
      blocks.push(
        <ol key={blocks.length} className={`list-decimal list-inside space-y-1 ${blockClass} mb-3`}>
          {listItems.map((item, idx) => (
            <li key={idx}>{parseBoldText(item)}</li>
          ))}
        </ol>
      );
      continue;
    }
    // Bullet list (• or - or *)
    if (/^[•\-*]\s/.test(trimmedLine) || /^\*\s/.test(trimmedLine)) {
      const listItems = [];
      while (i < lines.length && (/^[•\-*]\s/.test(lines[i].trim()) || /^\*\s/.test(lines[i].trim()))) {
        listItems.push(lines[i].trim().replace(/^[•\-*]\s*/, ""));
        i++;
      }
      blocks.push(
        <ul key={blocks.length} className={`list-disc list-inside space-y-1 ${blockClass} mb-3`}>
          {listItems.map((item, idx) => (
            <li key={idx}>{parseBoldText(item)}</li>
          ))}
        </ul>
      );
      continue;
    }
    // Paragraph: take consecutive non-empty, non-list lines
    const paraLines = [];
    while (i < lines.length) {
      const l = lines[i].trim();
      if (!l || /^\d+[.)]\s/.test(l) || /^[•\-*]\s/.test(l) || /^\*\s/.test(l)) break;
      paraLines.push(lines[i]);
      i++;
    }
    if (paraLines.length > 0) {
      blocks.push(
        <p key={blocks.length} className={`${blockClass} whitespace-pre-wrap mb-3`}>
          {parseBoldText(paraLines.join("\n"))}
        </p>
      );
    }
  }

  if (blocks.length === 0) {
    return (
      <p className={`${blockClass} whitespace-pre-wrap`}>
        {parseBoldText(trimmed)}
      </p>
    );
  }
  return <div className="space-y-1">{blocks}</div>;
};

/**
 * Classroom Guidance Response
 * For classroom management strategies and pedagogical guidance
 */
const ClassroomGuidanceResponse = ({ data }) => (
  <div className="space-y-4">
    {/* Situation Analysis */}
    {data.situation_analysis && (
      <div className="bg-white border-2 border-[#000000] p-5 rounded-lg shadow-[3px_3px_0px_0px_#000000]">
        <h4 className="text-lg font-bold text-[#000000] mb-3 flex items-center gap-2">
          <Info size={20} /> Understanding the Situation
        </h4>
        <p className="text-sm text-[#000000] leading-relaxed">
          {parseBoldText(data.situation_analysis)}
        </p>
      </div>
    )}

    {/* Immediate Tips */}
    {data.immediate_tips && data.immediate_tips.length > 0 && (
      <div className="bg-[#FDE047] border-2 border-[#000000] p-5 rounded-lg shadow-[3px_3px_0px_0px_#000000]">
        <h4 className="text-lg font-bold text-[#000000] mb-3 flex items-center gap-2">
          <Zap size={20} /> Quick Tips (Try Today!)
        </h4>
        <div className="space-y-3">
          {data.immediate_tips.map((tip, idx) => (
            <div
              key={idx}
              className="flex gap-3 bg-white border-2 border-[#000000] p-3 rounded"
            >
              <span className="flex-shrink-0 w-7 h-7 bg-[#FDE047] border-2 border-[#000000] rounded-full flex items-center justify-center text-sm font-bold">
                {idx + 1}
              </span>
              <p className="text-sm text-[#000000] flex-1 pt-0.5">{parseBoldText(tip)}</p>
            </div>
          ))}
        </div>
      </div>
    )}

    {/* Step-by-Step Strategies */}
    {data.step_by_step_strategies && data.step_by_step_strategies.length > 0 && (
      <div className="space-y-4">
        <h4 className="text-lg font-bold text-[#000000] flex items-center gap-2">
          <Target size={20} /> Detailed Strategies
        </h4>
        {data.step_by_step_strategies.map((strategy, idx) => (
          <div
            key={idx}
            className="bg-[#E0EEEF] border-2 border-[#000000] p-5 rounded-lg shadow-[3px_3px_0px_0px_#000000]"
          >
            <h5 className="font-bold text-[#000000] mb-2 flex items-center gap-2">
              <Presentation size={18} /> {strategy.strategy_name}
            </h5>
            
            <div className="space-y-2 mb-3">
              {strategy.steps && strategy.steps.map((step, stepIdx) => (
                <div key={stepIdx} className="flex gap-2 items-start">
                  <span className="flex-shrink-0 w-6 h-6 bg-white border-2 border-[#000000] rounded-full flex items-center justify-center text-xs font-bold">
                    {stepIdx + 1}
                  </span>
                  <p className="text-sm text-[#000000] pt-0.5">{parseBoldText(step)}</p>
                </div>
              ))}
            </div>

            {strategy.why_it_works && (
              <div className="mt-3 pt-3 border-t-2 border-[#000000]">
                <p className="text-xs font-bold text-[#000000] mb-1 flex items-center gap-1">
                  <Lightbulb size={14} /> Why It Works:
                </p>
                <p className="text-sm text-[#000000] italic">
                  {parseBoldText(strategy.why_it_works)}
                </p>
              </div>
            )}
          </div>
        ))}
      </div>
    )}

    {/* Long-term Approach */}
    {data.long_term_approach && (
      <div className="bg-[#D4F1C5] border-2 border-[#000000] p-5 rounded-lg shadow-[3px_3px_0px_0px_#000000]">
        <h4 className="text-lg font-bold text-[#000000] mb-3 flex items-center gap-2">
          <Target size={20} /> Long-term Approach
        </h4>
        <p className="text-sm text-[#000000] leading-relaxed">
          {parseBoldText(data.long_term_approach)}
        </p>
      </div>
    )}

    {/* Rural Adaptations */}
    {data.rural_adaptations && (
      <div className="bg-[#E8D5FF] border-2 border-[#000000] p-5 rounded-lg shadow-[3px_3px_0px_0px_#000000]">
        <h4 className="text-lg font-bold text-[#000000] mb-3 flex items-center gap-2">
          <Flower2 size={20} /> Rural Context Adaptations
        </h4>
        <p className="text-sm text-[#000000] leading-relaxed">
          {parseBoldText(data.rural_adaptations)}
        </p>
      </div>
    )}

    {/* Encouragement */}
    {data.encouragement && (
      <div className="bg-gradient-to-r from-[#F99DA8] to-[#FDE047] border-2 border-[#000000] p-5 rounded-lg shadow-[3px_3px_0px_0px_#000000]">
        <h4 className="text-lg font-bold text-[#000000] mb-3 flex items-center gap-2">
          <Heart size={20} /> You've Got This!
        </h4>
        <p className="text-sm text-[#000000] leading-relaxed">
          {parseBoldText(data.encouragement)}
        </p>
      </div>
    )}
  </div>
);

const TeacherMotivationResponse = ({ data }) => (
  <div className="space-y-4">
    {/* Title */}
    <div className="bg-gradient-to-r from-[#E8D5FF] to-[#DDD6FE] border-2 border-[#000000] p-6 rounded-lg shadow-[4px_4px_0px_0px_#000000]">
      <h3 className="text-2xl font-bold text-[#000000] mb-3 flex items-center gap-2">
        {data.motivation_title}
      </h3>
      <p className="text-base text-[#000000] leading-relaxed italic">
        {parseBoldText(data.acknowledgment)}
      </p>
    </div>

    {/* Immediate Tips */}
    {data.immediate_tips && data.immediate_tips.length > 0 && (
      <div className="bg-[#FDE047] border-2 border-[#000000] p-5 rounded-lg shadow-[3px_3px_0px_0px_#000000]">
        <h4 className="text-lg font-bold text-[#000000] mb-3 flex items-center gap-2">
          <Rocket size={20} /> Immediate Tips (Use Today!)
        </h4>
        <div className="space-y-3">
          {data.immediate_tips.map((tip, idx) => (
            <div
              key={idx}
              className="flex gap-3 bg-white border-2 border-[#000000] p-3 rounded"
            >
              <span className="flex-shrink-0 w-7 h-7 bg-[#FDE047] border-2 border-[#000000] rounded-full flex items-center justify-center text-sm font-bold">
                {idx + 1}
              </span>
              <p className="text-sm text-[#000000] flex-1 pt-0.5">{parseBoldText(tip)}</p>
            </div>
          ))}
        </div>
      </div>
    )}

    {/* Long-term Strategies */}
    {data.long_term_strategies && data.long_term_strategies.length > 0 && (
      <div className="bg-[#D4F1C5] border-2 border-[#000000] p-5 rounded-lg shadow-[3px_3px_0px_0px_#000000]">
        <h4 className="text-lg font-bold text-[#000000] mb-3 flex items-center gap-2">
          <Target size={20} /> Long-term Strategies
        </h4>
        <ul className="space-y-2">
          {data.long_term_strategies.map((strategy, idx) => (
            <li key={idx} className="flex items-start gap-3">
              <span className="text-[#000000] text-lg">✓</span>
              <span className="text-sm text-[#000000] flex-1">{parseBoldText(strategy)}</span>
            </li>
          ))}
        </ul>
      </div>
    )}

    {/* Inspiration */}
    {data.inspiration && (
      <div className="bg-gradient-to-r from-[#F99DA8] to-[#FDE047] border-2 border-[#000000] p-5 rounded-lg shadow-[3px_3px_0px_0px_#000000]">
        <h4 className="text-lg font-bold text-[#000000] mb-3 flex items-center gap-2">
          <Sparkles size={20} /> Remember This
        </h4>
        <p className="text-base text-[#000000] leading-relaxed font-medium">
          {parseBoldText(data.inspiration)}
        </p>
      </div>
    )}

    {/* Self-care Practices */}
    {data.self_care_practices && data.self_care_practices.length > 0 && (
      <div className="bg-[#E0EEEF] border-2 border-[#000000] p-5 rounded-lg shadow-[3px_3px_0px_0px_#000000]">
        <h4 className="text-lg font-bold text-[#000000] mb-3 flex items-center gap-2">
          <Flower2 size={20} /> Self-care Practices
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {data.self_care_practices.map((practice, idx) => (
            <div
              key={idx}
              className="flex items-start gap-2 bg-white border border-[#000000] p-3 rounded"
            >
              <span className="text-[#000000]">•</span>
              <span className="text-sm text-[#000000]">{parseBoldText(practice)}</span>
            </div>
          ))}
        </div>
      </div>
    )}

    {/* Perspective Shifts */}
    {data.perspective_shifts && data.perspective_shifts.length > 0 && (
      <div className="bg-white border-2 border-[#000000] p-5 rounded-lg shadow-[3px_3px_0px_0px_#000000]">
        <h4 className="text-lg font-bold text-[#000000] mb-3 flex items-center gap-2">
          <RotateCcw size={20} /> Perspective Shifts
        </h4>
        <ul className="space-y-2">
          {data.perspective_shifts.map((shift, idx) => (
            <li key={idx} className="flex items-start gap-3">
              <span className="text-[#000000] text-lg">→</span>
              <span className="text-sm text-[#000000] flex-1">{parseBoldText(shift)}</span>
            </li>
          ))}
        </ul>
      </div>
    )}
  </div>
);

const CrisisHandlerResponse = ({ data }) => (
  <div className="space-y-4">
    {/* Crisis Title */}
    {data.crisis_type && (
      <div className="bg-[#F99DA8] border-2 border-[#000000] p-5 rounded-lg shadow-[3px_3px_0px_0px_#000000]">
        <h3 className="text-xl font-bold text-[#000000] mb-2 flex items-center gap-2">
          <Info size={20} /> Crisis: {data.crisis_type}
        </h3>
        {data.severity && (
          <span className="inline-block bg-white border-2 border-[#000000] px-3 py-1 rounded text-sm font-bold">
            Severity: {data.severity}
          </span>
        )}
      </div>
    )}

    {/* Immediate Actions */}
    {data.immediate_actions && data.immediate_actions.length > 0 && (
      <div className="bg-[#FDE047] border-2 border-[#000000] p-5 rounded-lg shadow-[3px_3px_0px_0px_#000000]">
        <h4 className="text-lg font-bold text-[#000000] mb-3 flex items-center gap-2">
          <Zap size={20} /> Immediate Actions
        </h4>
        <ol className="space-y-3">
          {data.immediate_actions.map((action, idx) => (
            <li key={idx} className="flex gap-3">
              <span className="flex-shrink-0 w-7 h-7 bg-[#F99DA8] border-2 border-[#000000] rounded-full flex items-center justify-center text-sm font-bold">
                {idx + 1}
              </span>
              <span className="text-sm text-[#000000] flex-1 pt-0.5">
                {action}
              </span>
            </li>
          ))}
        </ol>
      </div>
    )}

    {/* De-escalation Techniques */}
    {data.deescalation_techniques &&
      data.deescalation_techniques.length > 0 && (
        <div className="bg-[#D4F1C5] border-2 border-[#000000] p-5 rounded-lg shadow-[3px_3px_0px_0px_#000000]">
          <h4 className="text-lg font-bold text-[#000000] mb-3 flex items-center gap-2">
            <Handshake size={20} /> De-escalation Techniques
          </h4>
          <ul className="space-y-2">
            {data.deescalation_techniques.map((technique, idx) => (
              <li key={idx} className="flex items-start gap-2">
                <span className="text-[#000000]">•</span>
                <span className="text-sm text-[#000000]">{parseBoldText(technique)}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

    {/* Prevention Strategies */}
    {data.prevention_strategies && data.prevention_strategies.length > 0 && (
      <div className="bg-[#E8D5FF] border-2 border-[#000000] p-5 rounded-lg shadow-[3px_3px_0px_0px_#000000]">
        <h4 className="text-lg font-bold text-[#000000] mb-3 flex items-center gap-2">
          <ShieldCheck size={20} /> Prevention Strategies
        </h4>
        <ul className="space-y-2">
          {data.prevention_strategies.map((strategy, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <span className="text-[#000000]">✓</span>
              <span className="text-sm text-[#000000]">{parseBoldText(strategy)}</span>
            </li>
          ))}
        </ul>
      </div>
    )}

    {/* Follow-up Actions */}
    {data.followup_actions && data.followup_actions.length > 0 && (
      <div className="bg-white border-2 border-[#000000] p-5 rounded-lg shadow-[3px_3px_0px_0px_#000000]">
        <h4 className="text-lg font-bold text-[#000000] mb-3 flex items-center gap-2">
          <Check size={20} /> Follow-up Actions
        </h4>
        <ul className="space-y-2">
          {data.followup_actions.map((action, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <span className="text-[#000000]">→</span>
              <span className="text-sm text-[#000000]">{parseBoldText(action)}</span>
            </li>
          ))}
        </ul>
      </div>
    )}
  </div>
);

/**
 * Feedback Response
 * For responding to teacher feedback about activities and lessons
 */
const FeedbackResponseComponent = ({ data }) => {
  const response = data.response || "";
  const sentiment = data.sentiment || "unclear";
  const followUpQuestions = data.follow_up_questions || [];
  const quickSuggestions = data.quick_suggestions || [];

  // Sentiment colors and icons
  const sentimentConfig = {
    positive: {
      color: "#A7F3D0",
      icon: <ThumbsUp size={20} className="text-[#000000]" />,
      label: "Positive Feedback"
    },
    negative: {
      color: "#FED7E2",
      icon: <ThumbsDown size={20} className="text-[#000000]" />,
      label: "Constructive Feedback"
    },
    mixed: {
      color: "#FDE047",
      icon: <MessageCircle size={20} className="text-[#000000]" />,
      label: "Mixed Feedback"
    },
    unclear: {
      color: "#E0EEEF",
      icon: <HelpCircle size={20} className="text-[#000000]" />,
      label: "Feedback Received"
    }
  };

  const config = sentimentConfig[sentiment] || sentimentConfig.unclear;

  return (
    <div className="space-y-4">
      {/* Main Response with Sentiment */}
      <div
        className="border-2 border-[#000000] p-5 rounded-lg shadow-[3px_3px_0px_0px_#000000]"
        style={{ backgroundColor: config.color }}
      >
        <div className="flex items-start gap-3 mb-3">
          <div className="mt-1">{config.icon}</div>
          <div className="flex-1">
            <div className="text-xs font-bold text-[#000000] opacity-70 uppercase tracking-wide mb-2">
              {config.label}
            </div>
          </div>
        </div>
        <p className="text-base text-[#000000] leading-relaxed">
          {parseBoldText(response)}
        </p>
      </div>

      {/* Follow-up Questions */}
      {followUpQuestions && followUpQuestions.length > 0 && (
        <div className="bg-[#E8D5FF] border-2 border-[#000000] p-5 rounded-lg shadow-[3px_3px_0px_0px_#000000]">
          <h4 className="text-lg font-bold text-[#000000] mb-3 flex items-center gap-2">
            <HelpCircle size={20} /> Let me understand better
          </h4>
          <ul className="space-y-2">
            {followUpQuestions.map((question, idx) => (
              <li key={idx} className="flex items-start gap-3">
                <span className="flex-shrink-0 w-6 h-6 bg-white border-2 border-[#000000] rounded-full flex items-center justify-center text-xs font-bold">
                  ?
                </span>
                <span className="text-sm text-[#000000] flex-1 pt-0.5">
                  {parseBoldText(question)}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Quick Suggestions */}
      {quickSuggestions && quickSuggestions.length > 0 && (
        <div className="bg-[#D4F1C5] border-2 border-[#000000] p-5 rounded-lg shadow-[3px_3px_0px_0px_#000000]">
          <h4 className="text-lg font-bold text-[#000000] mb-3 flex items-center gap-2">
            <Lightbulb size={20} /> Quick Suggestions to Try
          </h4>
          <div className="space-y-3">
            {quickSuggestions.map((suggestion, idx) => (
              <div
                key={idx}
                className="flex gap-3 bg-white border-2 border-[#000000] p-3 rounded"
              >
                <span className="flex-shrink-0 w-7 h-7 bg-[#D4F1C5] border-2 border-[#000000] rounded-full flex items-center justify-center text-sm font-bold">
                  {idx + 1}
                </span>
                <p className="text-sm text-[#000000] flex-1 pt-0.5">
                  {parseBoldText(suggestion)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Encouragement Footer */}
      <div className="bg-gradient-to-r from-[#FDE047] to-[#A7F3D0] border-2 border-[#000000] p-4 rounded-lg">
        <p className="text-sm text-[#000000] text-center font-medium">
          💡 Your feedback helps me learn and improve! Feel free to share more details.
        </p>
      </div>
    </div>
  );
};

/**
 * Web Search Response
 * For displaying web search results with AI summary and categorized resources
 */
const WebSearchResponse = ({ data }) => {
  const query = data.query || "";
  const summary = data.summary || "";
  const webResources = data.web_resources || [];
  const videoResources = data.video_resources || [];
  const educationalResources = data.educational_resources || [];
  const totalResults = data.total_results || 0;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-[#BFDBFE] border-2 border-[#000000] p-4 rounded-lg shadow-[3px_3px_0px_0px_#000000]">
        <div className="flex items-start gap-3">
          <div className="mt-1">
            <Search size={24} className="text-[#000000]" />
          </div>
          <div className="flex-1">
            <div className="text-xs font-bold text-[#000000] opacity-70 uppercase tracking-wide mb-1">
              Web Search Results
            </div>
            <h3 className="text-lg font-bold text-[#000000] mb-2">{query}</h3>
            {totalResults > 0 && (
              <div className="text-xs text-[#000000] opacity-60">
                Found {totalResults} resources
              </div>
            )}
          </div>
        </div>
      </div>

      {/* AI Summary */}
      {summary && (
        <div className="bg-[#FEF08A] border-2 border-[#000000] p-4 rounded-lg">
          <h4 className="font-bold text-[#000000] mb-2 flex items-center gap-2 text-sm">
            <Sparkles size={16} /> Summary
          </h4>
          <p className="text-sm text-[#000000] leading-relaxed">
            {parseBoldText(summary)}
          </p>
        </div>
      )}

      {/* Video Resources */}
      {videoResources.length > 0 && (
        <div className="bg-[#FBCFE8] border-2 border-[#000000] p-4 rounded-lg">
          <h4 className="font-bold text-[#000000] mb-3 flex items-center gap-2 text-sm">
            <Video size={16} /> Educational Videos
          </h4>
          <div className="space-y-2">
            {videoResources.map((resource, idx) => (
              <a
                key={idx}
                href={resource.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block border-2 border-[#000000] rounded-lg p-3 bg-white hover:bg-[#FFF1F2] transition-colors shadow-[2px_2px_0px_0px_#000000] hover:shadow-[3px_3px_0px_0px_#000000] hover:-translate-y-0.5"
              >
                <div className="flex items-start gap-2">
                  <Video size={16} className="text-[#000000] mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm text-[#000000] line-clamp-2 flex items-center gap-1">
                      {resource.title}
                      <ExternalLink size={12} className="flex-shrink-0 opacity-60" />
                    </div>
                    {resource.description && (
                      <p className="text-xs text-[#000000] opacity-70 mt-1 line-clamp-2">
                        {resource.description}
                      </p>
                    )}
                  </div>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Educational Resources */}
      {educationalResources.length > 0 && (
        <div className="bg-[#A7F3D0] border-2 border-[#000000] p-4 rounded-lg">
          <h4 className="font-bold text-[#000000] mb-3 flex items-center gap-2 text-sm">
            <FileText size={16} /> Educational Materials
          </h4>
          <div className="space-y-2">
            {educationalResources.map((resource, idx) => (
              <a
                key={idx}
                href={resource.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block border-2 border-[#000000] rounded-lg p-3 bg-white hover:bg-[#F0FDF4] transition-colors shadow-[2px_2px_0px_0px_#000000] hover:shadow-[3px_3px_0px_0px_#000000] hover:-translate-y-0.5"
              >
                <div className="flex items-start gap-2">
                  <FileText size={16} className="text-[#000000] mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm text-[#000000] line-clamp-2 flex items-center gap-1">
                      {resource.title}
                      <ExternalLink size={12} className="flex-shrink-0 opacity-60" />
                    </div>
                    {resource.description && (
                      <p className="text-xs text-[#000000] opacity-70 mt-1 line-clamp-2">
                        {resource.description}
                      </p>
                    )}
                  </div>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Web Articles */}
      {webResources.length > 0 && (
        <div className="bg-[#DDD6FE] border-2 border-[#000000] p-4 rounded-lg">
          <h4 className="font-bold text-[#000000] mb-3 flex items-center gap-2 text-sm">
            <Globe size={16} /> Related Articles
          </h4>
          <div className="space-y-2">
            {webResources.map((resource, idx) => (
              <a
                key={idx}
                href={resource.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block border-2 border-[#000000] rounded-lg p-3 bg-white hover:bg-[#FAF5FF] transition-colors shadow-[2px_2px_0px_0px_#000000] hover:shadow-[3px_3px_0px_0px_#000000] hover:-translate-y-0.5"
              >
                <div className="flex items-start gap-2">
                  <Globe size={16} className="text-[#000000] mt-0.5 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm text-[#000000] line-clamp-2 flex items-center gap-1">
                      {resource.title}
                      <ExternalLink size={12} className="flex-shrink-0 opacity-60" />
                    </div>
                    {resource.description && (
                      <p className="text-xs text-[#000000] opacity-70 mt-1 line-clamp-2">
                        {resource.description}
                      </p>
                    )}
                  </div>
                </div>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* No Results */}
      {totalResults === 0 && (
        <div className="bg-[#F3F4F6] border-2 border-[#000000] p-4 rounded-lg text-center">
          <p className="text-sm text-[#000000] opacity-60">
            No search results found for this query.
          </p>
        </div>
      )}
    </div>
  );
};

/**
 * Resources Section Component
 * Displays videos, web links, and educational resources from Tavily search
 */
const ResourcesSection = ({ resources }) => {
  if (!resources || resources.total_results === 0) return null;

  const { video_resources = [], web_resources = [], educational_resources = [] } = resources;

  const hasVideos = video_resources.length > 0;
  const hasWebResources = web_resources.length > 0;
  const hasEducationalResources = educational_resources.length > 0;

  if (!hasVideos && !hasWebResources && !hasEducationalResources) return null;

  const ResourceCard = ({ resource, icon: Icon, bgColor }) => (
    <a
      href={resource.url}
      target="_blank"
      rel="noopener noreferrer"
      className="block border-2 border-[#000000] rounded-lg p-3 shadow-[2px_2px_0px_0px_#000000] hover:shadow-[4px_4px_0px_0px_#000000] hover:-translate-y-0.5 transition-all duration-150"
      style={{ backgroundColor: bgColor }}
    >
      <div className="flex items-start gap-2">
        <Icon size={16} className="text-[#000000] mt-0.5 flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="font-medium text-sm text-[#000000] line-clamp-2 flex items-center gap-1">
            {resource.title}
            <ExternalLink size={12} className="flex-shrink-0 opacity-60" />
          </div>
          {resource.description && (
            <p className="text-xs text-[#000000] opacity-70 mt-1 line-clamp-2">
              {resource.description}
            </p>
          )}
        </div>
      </div>
    </a>
  );

  return (
    <div className="mt-6 pt-4 border-t-2 border-[#000000] border-dashed">
      <h3 className="text-lg font-bold text-[#000000] mb-4 flex items-center gap-2">
        <Globe size={20} /> Additional Resources
      </h3>

      {/* Video Resources */}
      {hasVideos && (
        <div className="mb-4">
          <h4 className="text-sm font-bold text-[#000000] mb-2 flex items-center gap-2">
            <Video size={16} /> Videos
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {video_resources.slice(0, 4).map((resource, idx) => (
              <ResourceCard key={idx} resource={resource} icon={Video} bgColor="#FEE2E2" />
            ))}
          </div>
        </div>
      )}

      {/* Web Resources */}
      {hasWebResources && (
        <div className="mb-4">
          <h4 className="text-sm font-bold text-[#000000] mb-2 flex items-center gap-2">
            <Globe size={16} /> Web Articles
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {web_resources.slice(0, 4).map((resource, idx) => (
              <ResourceCard key={idx} resource={resource} icon={Globe} bgColor="#DBEAFE" />
            ))}
          </div>
        </div>
      )}

      {/* Educational Resources */}
      {hasEducationalResources && (
        <div className="mb-4">
          <h4 className="text-sm font-bold text-[#000000] mb-2 flex items-center gap-2">
            <FileText size={16} /> Educational Materials
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {educational_resources.slice(0, 4).map((resource, idx) => (
              <ResourceCard key={idx} resource={resource} icon={FileText} bgColor="#D1FAE5" />
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * Main ResponseFormatter Component
 */
/**
 * Resource-finder style response: summary + optional resource lists
 */
const ResourceFinderResponse = ({ data }) => {
  const summary = data?.summary ?? "";
  return (
    <div className="space-y-4">
      {summary ? (
        <div className="border-2 border-[#000000] p-5 rounded-lg shadow-[3px_3px_0px_0px_#000000] bg-[#DBEAFE]">
          <p className="text-sm md:text-base text-[#000000] leading-relaxed">
            {parseBoldText(summary)}
          </p>
        </div>
      ) : null}
    </div>
  );
};

const ResponseFormatter = ({ toolUsed, result, text, resources }) => {
  // If result is missing but text looks like stringified resource-finder JSON, parse and render
  let effectiveResult = result;
  let effectiveResources = resources;
  if ((!result || typeof result !== "object") && typeof text === "string" && text.trim().startsWith("{")) {
    try {
      const parsed = JSON.parse(text);
      if (parsed && typeof parsed === "object" && "summary" in parsed) {
        effectiveResult = parsed;
        effectiveResources = effectiveResources || parsed;
      }
    } catch (_) {
      // not JSON or invalid, keep default rendering
    }
  }

  // For resource_finder, result itself holds web_resources/video_resources/educational_resources;
  // when loading from history, resources may be missing, so use result as resources for the section
  if (!effectiveResources && effectiveResult && typeof effectiveResult === "object") {
    const hasResourceArrays =
      (effectiveResult.web_resources?.length ?? 0) > 0 ||
      (effectiveResult.video_resources?.length ?? 0) > 0 ||
      (effectiveResult.educational_resources?.length ?? 0) > 0;
    if (hasResourceArrays) {
      effectiveResources = effectiveResult;
    }
  }

  if (!effectiveResult || typeof effectiveResult !== "object") {
    return <DefaultResponse text={text} />;
  }

  // Helper to wrap response with resources section
  const withResources = (component) => (
    <div>
      {component}
      <ResourcesSection resources={effectiveResources} />
    </div>
  );

  // Format based on tool type
  switch (toolUsed) {
    case "quick_answer":
      return withResources(<QuickAnswerResponse data={effectiveResult} />);

    case "general_conversation":
      return withResources(<GeneralConversationResponse data={effectiveResult} />);

    case "activity_generator":
      return withResources(<ActivityResponse data={effectiveResult} />);

    case "expert_teacher":
      return withResources(<ExpertTeacherResponse data={effectiveResult} />);

    case "content_explainer":
      return withResources(<ContentExplanationResponse data={effectiveResult} />);

    case "teacher_motivation":
      return withResources(<TeacherMotivationResponse data={effectiveResult} />);

    case "crisis_handler":
      // Crisis handler returns activity-like structure
      if (effectiveResult.activity_name) {
        return withResources(<ActivityResponse data={effectiveResult} />);
      }
      return withResources(<CrisisHandlerResponse data={effectiveResult} />);

    case "classroom_guidance":
      return withResources(<ClassroomGuidanceResponse data={effectiveResult} />);

    case "feedback_response":
      return withResources(<FeedbackResponseComponent data={effectiveResult} />);

    case "vision_analysis":
      // Vision analysis response - display as general conversation with image context
      return withResources(
        <GeneralConversationResponse 
          data={{
            response_type: "general",
            response: effectiveResult.response || text,
            suggested_topics: []
          }} 
        />
      );

    case "document_ready":
      // PDF document uploaded and compiled; show summary (scrollable) and fixed "ask questions" hint
      return (
        <div className="space-y-4">
          <div
            className="border-2 border-[#000000] p-6 rounded-lg shadow-[3px_3px_0px_0px_#000000] max-h-[60vh] flex flex-col"
            style={{ backgroundColor: "#D1FAE5" }}
          >
            <div className="flex items-start gap-3 flex-shrink-0">
              <div className="mt-1">
                <FileText size={24} className="text-[#000000]" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-bold text-[#000000] opacity-70 uppercase tracking-wide mb-2">
                  Document ready
                </div>
              </div>
            </div>
            <div className="flex-1 min-h-0 overflow-y-auto mt-1">
              <p className="text-[#000000] leading-relaxed whitespace-pre-wrap">
                {parseBoldText(effectiveResult.summary || text || "You can ask questions about this document.")}
              </p>
            </div>
            <p className="text-sm text-[#000000] opacity-70 mt-3 flex-shrink-0">
              Ask questions in the chat and I will answer using only this document.
            </p>
          </div>
        </div>
      );

    case "document_qa":
      // Answer from uploaded document
      return withResources(
        <GeneralConversationResponse
          data={{
            response_type: "general",
            response: effectiveResult.response || text,
            suggested_topics: []
          }}
        />
      );

    case "resource_finder":
      return withResources(<ResourceFinderResponse data={effectiveResult} />);

    default:
      // Parsed JSON may be resource-finder shape without tool_used set
      if (effectiveResult.summary != null && (effectiveResult.web_resources != null || effectiveResult.video_resources != null || effectiveResult.educational_resources != null)) {
        return withResources(<ResourceFinderResponse data={effectiveResult} />);
      }
      return withResources(<DefaultResponse text={text} />);
  }
};

export default ResponseFormatter;
