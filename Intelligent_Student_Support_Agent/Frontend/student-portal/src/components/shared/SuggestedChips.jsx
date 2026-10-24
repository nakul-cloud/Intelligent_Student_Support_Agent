import React from 'react';
import { CreditCard, Award, Calendar, HelpCircle, ArrowUpRight, UserCheck } from 'lucide-react';

/**
 * SuggestedChips Component
 * Clean, modern starter prompt cards matching ChatGPT & Claude aesthetic.
 */
export default function SuggestedChips({ onSelect }) {
  const cards = [
    {
      title: 'Tuition & Fees Status',
      desc: 'Check pending balance, receipts, and payment deadlines',
      prompt: 'What is my current fee status and how much do I still owe?',
      icon: CreditCard,
    },
    {
      title: 'Scholarship Details',
      desc: 'View active grant percentage, amount, and renewal rules',
      prompt: 'Do I qualify for a scholarship and what are the renewal rules?',
      icon: Award,
    },
    {
      title: 'Update Profile & Contact',
      desc: 'Instantly update phone, campus hostel address, or password',
      prompt: 'I want to update my phone number and campus address in my student profile.',
      icon: UserCheck,
    },
    {
      title: 'Grading & Academic Policy',
      desc: 'Learn about course grade points, SGPA, and exam criteria',
      prompt: 'How does the grading system work in my programme?',
      icon: Calendar,
    },
    {
      title: 'Attendance Requirements',
      desc: 'Find out the minimum attendance percentage for end-term exams',
      prompt: 'What is the attendance policy and minimum attendance required for exams?',
      icon: HelpCircle,
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl mx-auto mt-4">
      {cards.map((item, idx) => {
        const Icon = item.icon;
        return (
          <button
            key={idx}
            type="button"
            onClick={() => onSelect(item.prompt)}
            className="group flex flex-col items-start p-4 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 hover:border-slate-300 transition-[transform,border-color,background-color,box-shadow] duration-160 ease-out text-left shadow-xs hover:shadow-sm active:scale-[0.97]"
          >
            <div className="flex items-center justify-between w-full mb-2">
              <div className="w-8 h-8 rounded-lg bg-slate-100 border border-slate-200/80 flex items-center justify-center text-slate-700 group-hover:bg-slate-900 group-hover:text-white transition-[background-color,color] duration-160 ease-out">
                <Icon className="w-4 h-4" />
              </div>
              <ArrowUpRight className="w-4 h-4 text-slate-400 group-hover:text-slate-900 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-[color,transform] duration-160 ease-out" />
            </div>

            <p className="text-sm font-bold text-slate-800 group-hover:text-slate-950 transition-colors">
              {item.title}
            </p>

            <p className="text-xs text-slate-500 mt-1 leading-snug">
              {item.desc}
            </p>
          </button>
        );
      })}
    </div>
  );
}
