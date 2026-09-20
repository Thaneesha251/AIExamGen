import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  CheckCircle2,
  AlertTriangle,
  HelpCircle,
  FileText,
  Filter,
  Search,
  ChevronRight,
  ShieldAlert,
  Award,
  BookOpen,
  PieChart,
  RefreshCw,
  Edit3
} from 'lucide-react';
import { questionQualityService } from '@/services/questionQualityService';
import {
  ExamQualityDashboard,
  QuestionQualityItem,
  BlueprintBalance
} from '@/types/questionQuality';
import { apiClient } from '@/services/api';

export const ExamQualityPage: React.FC = () => {
  const [examinations, setExaminations] = useState<any[]>([]);
  const [selectedExamId, setSelectedExamId] = useState<string>('');
  const [dashboard, setDashboard] = useState<ExamQualityDashboard | null>(null);
  const [blueprint, setBlueprint] = useState<BlueprintBalance | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Filters & Search
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Selected Question Modal
  const [selectedQuestion, setSelectedQuestion] = useState<QuestionQualityItem | null>(null);
  const [reviewModalOpen, setReviewModalOpen] = useState<boolean>(false);
  const [reviewStatus, setReviewStatus] = useState<'KEEP' | 'REVIEW_BEFORE_REUSE' | 'REVIEWED'>('KEEP');
  const [reviewNote, setReviewNote] = useState<string>('');
  const [savingReview, setSavingReview] = useState<boolean>(false);

  useEffect(() => {
    fetchExaminations();
  }, []);

  const fetchExaminations = async () => {
    try {
      const res = await apiClient.get('/academic/examinations');
      const data = res.data?.data || res.data || [];
      setExaminations(Array.isArray(data) ? data : []);
      if (Array.isArray(data) && data.length > 0) {
        setSelectedExamId(data[0].id);
        loadDashboard(data[0].id);
      }
    } catch (err: any) {
      // Fallback dummy exam list if none returned
      console.error('Failed to load examinations', err);
    }
  };

  const loadDashboard = async (examId: string) => {
    if (!examId) return;
    setLoading(true);
    setError(null);
    try {
      const dashData = await questionQualityService.getExamQualityDashboard(examId);
      setDashboard(dashData);

      try {
        const bpData = await questionQualityService.getExamBlueprintBalance(examId);
        setBlueprint(bpData);
      } catch (bpErr) {
        setBlueprint(null);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load exam quality analytics');
      setDashboard(null);
    } finally {
      setLoading(false);
    }
  };

  const handleExamChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value;
    setSelectedExamId(id);
    loadDashboard(id);
  };

  const openQuestionReview = (q: QuestionQualityItem) => {
    setSelectedQuestion(q);
    setReviewStatus(q.faculty_review_status === 'REVIEW_BEFORE_REUSE' ? 'REVIEW_BEFORE_REUSE' : 'KEEP');
    setReviewNote(q.faculty_review_note || '');
    setReviewModalOpen(true);
  };

  const handleSaveReview = async () => {
    if (!selectedQuestion) return;
    setSavingReview(true);
    try {
      await questionQualityService.recordQuestionQualityReview(selectedQuestion.question_id, {
        examination_id: selectedExamId,
        status: reviewStatus,
        note: reviewNote
      });
      setReviewModalOpen(false);
      loadDashboard(selectedExamId);
    } catch (err: any) {
      alert(err.message || 'Failed to record review');
    } finally {
      setSavingReview(false);
    }
  };

  const filteredQuestions = (dashboard?.questions || []).filter((q) => {
    const matchesSearch =
      q.question_text.toLowerCase().includes(searchQuery.toLowerCase()) ||
      q.question_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      q.unit_title.toLowerCase().includes(searchQuery.toLowerCase());

    if (statusFilter === 'ALL') return matchesSearch;
    if (statusFilter === 'WARNINGS') return matchesSearch && q.quality_status !== 'GOOD';
    return matchesSearch && q.quality_status === statusFilter;
  });

  const getStatusBadge = (statusVal: string) => {
    switch (statusVal) {
      case 'GOOD':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Good Quality</span>;
      case 'REVIEW_DIFFICULTY':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20">Review Difficulty</span>;
      case 'REVIEW_DISCRIMINATION':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">Weak Discrimination</span>;
      case 'REVIEW_SIMILARITY':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">Similarity Flagged</span>;
      case 'REVIEW_MULTIPLE_SIGNALS':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-rose-600/20 text-rose-300 border border-rose-500/30 font-bold">Multiple Warnings</span>;
      case 'INSUFFICIENT_DATA':
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-slate-500/10 text-slate-400 border border-slate-500/20">Insufficient Data</span>;
      default:
        return <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-slate-500/10 text-slate-400">{statusVal}</span>;
    }
  };

  const getDiscriminationBadge = (cat: string, index: number | null) => {
    const valText = index !== null ? `(${index >= 0 ? '+' : ''}${index})` : '';
    switch (cat) {
      case 'STRONG':
        return <span className="text-emerald-400 font-medium">Strong {valText}</span>;
      case 'ACCEPTABLE':
        return <span className="text-blue-400 font-medium">Acceptable {valText}</span>;
      case 'WEAK':
        return <span className="text-amber-400 font-medium">Weak {valText}</span>;
      case 'NEGATIVE':
        return <span className="text-rose-400 font-bold">Negative {valText}</span>;
      default:
        return <span className="text-slate-400 text-xs">Insufficient Sample</span>;
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 text-slate-100">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-900/60 p-6 rounded-2xl border border-slate-800 backdrop-blur-xl shadow-xl">
        <div>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent">
            Exam Quality & Question Intelligence
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Post-evaluation difficulty, discrimination index, blueprint balance, and question quality insights.
          </p>
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <label className="text-sm font-medium text-slate-300 whitespace-nowrap">Examination:</label>
          <select
            value={selectedExamId}
            onChange={handleExamChange}
            className="w-full sm:w-64 bg-slate-800/80 border border-slate-700 text-slate-200 text-sm rounded-xl px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
          >
            {examinations.length === 0 && <option value="">No Examinations Found</option>}
            {examinations.map((ex) => (
              <option key={ex.id} value={ex.id}>
                {ex.name || ex.title}
              </option>
            ))}
          </select>
          <button
            onClick={() => loadDashboard(selectedExamId)}
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl transition border border-slate-700"
            title="Refresh Data"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 text-rose-300 p-4 rounded-xl flex items-center gap-3">
          <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {loading && !dashboard && (
        <div className="py-20 text-center text-slate-400 space-y-3">
          <RefreshCw className="w-8 h-8 animate-spin mx-auto text-indigo-400" />
          <p className="text-sm font-medium">Analyzing question quality statistics from finalized evaluations...</p>
        </div>
      )}

      {dashboard && (
        <>
          {/* Stats Overview */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 flex items-center gap-4">
              <div className="p-3 bg-blue-500/10 text-blue-400 rounded-xl border border-blue-500/20">
                <Award className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs text-slate-400 font-medium">Average Exam Score</p>
                <h3 className="text-xl font-bold text-slate-100">
                  {dashboard.average_exam_score} <span className="text-sm font-normal text-slate-400">({dashboard.average_exam_percentage}%)</span>
                </h3>
              </div>
            </div>

            <div className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 flex items-center gap-4">
              <div className="p-3 bg-indigo-500/10 text-indigo-400 rounded-xl border border-indigo-500/20">
                <FileText className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs text-slate-400 font-medium">Questions Analyzed</p>
                <h3 className="text-xl font-bold text-slate-100">{dashboard.questions_analyzed} / {dashboard.total_questions}</h3>
              </div>
            </div>

            <div className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 flex items-center gap-4">
              <div className="p-3 bg-emerald-500/10 text-emerald-400 rounded-xl border border-emerald-500/20">
                <CheckCircle2 className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs text-slate-400 font-medium">Finalized Student Papers</p>
                <h3 className="text-xl font-bold text-slate-100">{dashboard.finalized_responses}</h3>
              </div>
            </div>

            <div className="bg-slate-900/60 p-5 rounded-2xl border border-slate-800 flex items-center gap-4">
              <div className="p-3 bg-amber-500/10 text-amber-400 rounded-xl border border-amber-500/20">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div>
                <p className="text-xs text-slate-400 font-medium">Faculty Review Warnings</p>
                <h3 className="text-xl font-bold text-amber-400">{dashboard.questions_requiring_review}</h3>
              </div>
            </div>
          </div>

          {/* Distributions */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Difficulty Breakdown */}
            <div className="bg-slate-900/60 p-6 rounded-2xl border border-slate-800 space-y-4">
              <h3 className="text-base font-semibold text-slate-200 flex items-center gap-2">
                <PieChart className="w-4 h-4 text-indigo-400" />
                Difficulty Index Distribution
              </h3>
              <div className="space-y-3">
                {Object.entries(dashboard.difficulty_distribution).map(([cat, count]) => {
                  const pct = dashboard.questions_analyzed > 0 ? Math.round((count / dashboard.questions_analyzed) * 100) : 0;
                  return (
                    <div key={cat} className="space-y-1">
                      <div className="flex justify-between text-xs font-medium text-slate-300">
                        <span>{cat}</span>
                        <span>{count} questions ({pct}%)</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                        <div
                          className={`h-full transition-all duration-500 ${
                            cat === 'EASY' ? 'bg-emerald-400' : cat === 'MODERATE' ? 'bg-blue-400' : 'bg-rose-400'
                          }`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Discrimination Breakdown */}
            <div className="bg-slate-900/60 p-6 rounded-2xl border border-slate-800 space-y-4">
              <h3 className="text-base font-semibold text-slate-200 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-purple-400" />
                Discrimination Index Distribution (Top 27% vs Bottom 27%)
              </h3>
              <div className="space-y-3">
                {Object.entries(dashboard.discrimination_distribution).map(([cat, count]) => {
                  const pct = dashboard.questions_analyzed > 0 ? Math.round((count / dashboard.questions_analyzed) * 100) : 0;
                  return (
                    <div key={cat} className="space-y-1">
                      <div className="flex justify-between text-xs font-medium text-slate-300">
                        <span>{cat}</span>
                        <span>{count} questions ({pct}%)</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                        <div
                          className={`h-full transition-all duration-500 ${
                            cat === 'STRONG'
                              ? 'bg-emerald-400'
                              : cat === 'ACCEPTABLE'
                              ? 'bg-blue-400'
                              : cat === 'WEAK'
                              ? 'bg-amber-400'
                              : cat === 'NEGATIVE'
                              ? 'bg-rose-500'
                              : 'bg-slate-600'
                          }`}
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Blueprint Balance Section */}
          {blueprint && (
            <div className="bg-slate-900/60 p-6 rounded-2xl border border-slate-800 space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-base font-semibold text-slate-200 flex items-center gap-2">
                  <BookOpen className="w-4 h-4 text-blue-400" />
                  Blueprint Balance & Variance Analysis ({blueprint.blueprint_name})
                </h3>
                <span
                  className={`px-3 py-1 text-xs font-bold rounded-full ${
                    blueprint.overall_status === 'BALANCED'
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'
                  }`}
                >
                  {blueprint.overall_status} (Max Variance: {blueprint.max_variance}%)
                </span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs text-slate-300">
                  <thead className="bg-slate-800/60 text-slate-400 uppercase text-[10px]">
                    <tr>
                      <th className="p-3">Academic Unit / Category</th>
                      <th className="p-3 text-right">Target Weight %</th>
                      <th className="p-3 text-right">Actual Weight %</th>
                      <th className="p-3 text-right">Variance</th>
                      <th className="p-3 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {blueprint.breakdown.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition">
                        <td className="p-3 font-medium text-slate-200">{row.category_name}</td>
                        <td className="p-3 text-right">{row.target_percentage}%</td>
                        <td className="p-3 text-right font-semibold text-slate-100">{row.actual_percentage}%</td>
                        <td className={`p-3 text-right font-bold ${row.variance > 0 ? 'text-amber-400' : row.variance < 0 ? 'text-blue-400' : 'text-slate-400'}`}>
                          {row.variance > 0 ? `+${row.variance}%` : `${row.variance}%`}
                        </td>
                        <td className="p-3 text-center">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                              row.status === 'BALANCED'
                                ? 'bg-emerald-500/10 text-emerald-400'
                                : 'bg-amber-500/10 text-amber-400'
                            }`}
                          >
                            {row.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Question Quality Table */}
          <div className="bg-slate-900/60 p-6 rounded-2xl border border-slate-800 space-y-4">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
              <h3 className="text-base font-semibold text-slate-200 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-indigo-400" />
                Question Quality Analysis Table
              </h3>

              <div className="flex items-center gap-3 w-full sm:w-auto">
                <div className="relative w-full sm:w-64">
                  <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-500" />
                  <input
                    type="text"
                    placeholder="Search question text..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full bg-slate-800/80 border border-slate-700 text-slate-200 text-xs rounded-xl pl-9 pr-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>

                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="bg-slate-800/80 border border-slate-700 text-slate-200 text-xs rounded-xl px-3 py-2 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                >
                  <option value="ALL">All Statuses</option>
                  <option value="WARNINGS">Warnings Only</option>
                  <option value="GOOD">Good Quality</option>
                  <option value="REVIEW_DIFFICULTY">Review Difficulty</option>
                  <option value="REVIEW_DISCRIMINATION">Weak Discrimination</option>
                  <option value="REVIEW_SIMILARITY">Similarity Flagged</option>
                  <option value="REVIEW_MULTIPLE_SIGNALS">Multiple Warnings</option>
                </select>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-800/60 text-slate-400 uppercase text-[10px]">
                  <tr>
                    <th className="p-3">Q#</th>
                    <th className="p-3">Question Text</th>
                    <th className="p-3">Unit / Topic</th>
                    <th className="p-3 text-center">Difficulty</th>
                    <th className="p-3 text-right">Avg Score %</th>
                    <th className="p-3 text-center">Discrimination Index</th>
                    <th className="p-3 text-center">Quality Status</th>
                    <th className="p-3 text-center">Similarity Flags</th>
                    <th className="p-3 text-center">Faculty Review</th>
                    <th className="p-3 text-center">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {filteredQuestions.length === 0 && (
                    <tr>
                      <td colSpan={10} className="p-8 text-center text-slate-500">
                        No questions match the selected filter criteria.
                      </td>
                    </tr>
                  )}
                  {filteredQuestions.map((q) => (
                    <tr key={q.question_id} className="hover:bg-slate-800/30 transition">
                      <td className="p-3 font-bold text-slate-200">{q.question_number}</td>
                      <td className="p-3 max-w-xs truncate font-medium text-slate-100" title={q.question_text}>
                        {q.question_text}
                      </td>
                      <td className="p-3 text-slate-400">
                        <div>{q.unit_title}</div>
                        <div className="text-[10px] text-slate-500">{q.topic_name}</div>
                      </td>
                      <td className="p-3 text-center">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                            q.difficulty_category === 'EASY'
                              ? 'bg-emerald-500/10 text-emerald-400'
                              : q.difficulty_category === 'MODERATE'
                              ? 'bg-blue-500/10 text-blue-400'
                              : 'bg-rose-500/10 text-rose-400'
                          }`}
                        >
                          {q.difficulty_category}
                        </span>
                      </td>
                      <td className="p-3 text-right font-semibold text-slate-100">{q.average_percentage}%</td>
                      <td className="p-3 text-center">
                        {getDiscriminationBadge(q.discrimination_category, q.discrimination_index)}
                      </td>
                      <td className="p-3 text-center">{getStatusBadge(q.quality_status)}</td>
                      <td className="p-3 text-center">
                        {q.similarity_flag_count > 0 ? (
                          <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-purple-500/20 text-purple-300 border border-purple-500/30">
                            {q.similarity_flag_count} pairs
                          </span>
                        ) : (
                          <span className="text-slate-500">0</span>
                        )}
                      </td>
                      <td className="p-3 text-center">
                        <span
                          className={`px-2 py-0.5 text-[10px] font-medium rounded ${
                            q.faculty_review_status === 'KEEP'
                              ? 'bg-emerald-500/10 text-emerald-400'
                              : q.faculty_review_status === 'REVIEW_BEFORE_REUSE'
                              ? 'bg-amber-500/10 text-amber-400'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {q.faculty_review_status}
                        </span>
                      </td>
                      <td className="p-3 text-center">
                        <button
                          onClick={() => openQuestionReview(q)}
                          className="px-2.5 py-1 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 rounded-lg transition text-xs flex items-center gap-1 mx-auto border border-indigo-500/30"
                        >
                          <Edit3 className="w-3 h-3" />
                          Review
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}

      {/* Question Review Modal */}
      {reviewModalOpen && selectedQuestion && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 space-y-5 text-slate-100 shadow-2xl">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-lg font-bold text-slate-100">
                  Question Detail & Faculty Review ({selectedQuestion.question_number})
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">{selectedQuestion.unit_title}</p>
              </div>
              <button
                onClick={() => setReviewModalOpen(false)}
                className="text-slate-400 hover:text-slate-200 text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="bg-slate-800/60 p-4 rounded-xl border border-slate-700/60 text-xs space-y-2">
              <p className="font-semibold text-slate-200">{selectedQuestion.question_text}</p>
              <div className="flex flex-wrap gap-3 text-[11px] text-slate-400 pt-2 border-t border-slate-700/60">
                <span>Bloom: <strong className="text-slate-200">{selectedQuestion.bloom_level}</strong></span>
                <span>Max Marks: <strong className="text-slate-200">{selectedQuestion.max_marks}</strong></span>
                <span>Configured Difficulty: <strong className="text-slate-200">{selectedQuestion.configured_difficulty}</strong></span>
              </div>
            </div>

            {/* Quality Metrics */}
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="bg-slate-800/40 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-400">Average Percentage:</span>
                <p className="text-base font-bold text-slate-100 mt-1">{selectedQuestion.average_percentage}%</p>
                <span className="text-[10px] text-slate-500">Category: {selectedQuestion.difficulty_category}</span>
              </div>

              <div className="bg-slate-800/40 p-3 rounded-xl border border-slate-800">
                <span className="text-slate-400">Discrimination Index:</span>
                <p className="text-base font-bold text-indigo-400 mt-1">
                  {selectedQuestion.discrimination_index !== null ? selectedQuestion.discrimination_index : 'N/A'}
                </p>
                <span className="text-[10px] text-slate-500">Category: {selectedQuestion.discrimination_category}</span>
              </div>
            </div>

            {/* Review Controls */}
            <div className="space-y-3 pt-2">
              <label className="text-xs font-semibold text-slate-300 block">Faculty Review Status:</label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setReviewStatus('KEEP')}
                  className={`p-3 rounded-xl border text-xs font-semibold transition ${
                    reviewStatus === 'KEEP'
                      ? 'bg-emerald-500/20 border-emerald-500 text-emerald-300'
                      : 'bg-slate-800/60 border-slate-700 text-slate-400 hover:border-slate-600'
                  }`}
                >
                  ✓ Keep for Reuse
                </button>
                <button
                  type="button"
                  onClick={() => setReviewStatus('REVIEW_BEFORE_REUSE')}
                  className={`p-3 rounded-xl border text-xs font-semibold transition ${
                    reviewStatus === 'REVIEW_BEFORE_REUSE'
                      ? 'bg-amber-500/20 border-amber-500 text-amber-300'
                      : 'bg-slate-800/60 border-slate-700 text-slate-400 hover:border-slate-600'
                  }`}
                >
                  ⚠ Review Before Reuse
                </button>
              </div>

              <label className="text-xs font-semibold text-slate-300 block">Faculty Notes & Recommendations:</label>
              <textarea
                value={reviewNote}
                onChange={(e) => setReviewNote(e.target.value)}
                placeholder="Add faculty notes regarding question wording, difficulty calibration, or reuse advice..."
                rows={3}
                className="w-full bg-slate-800/80 border border-slate-700 rounded-xl p-3 text-xs text-slate-200 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              />
            </div>

            <div className="flex justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setReviewModalOpen(false)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs transition"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSaveReview}
                disabled={savingReview}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold transition flex items-center gap-2"
              >
                {savingReview ? 'Saving...' : 'Save Faculty Review'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExamQualityPage;
