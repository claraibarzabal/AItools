"""NLP analysis: topics, keywords, n-grams, clustering, and concept extraction."""

from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from dataclasses import dataclass

import nltk
import numpy as np
import pandas as pd
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from sklearn.cluster import KMeans
from sklearn.decomposition import NMF
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

from .config import AI_TOOLS, NLP_SETTINGS, SEO_CONCEPTS, WORKFLOW_PHRASES

logger = logging.getLogger(__name__)


def ensure_nltk_data() -> None:
    for resource in ("punkt", "punkt_tab", "stopwords", "wordnet", "omw-1.4"):
        nltk.download(resource, quiet=True)


@dataclass
class NLPAnalysisResult:
    top_keywords: pd.DataFrame
    top_ngrams: pd.DataFrame
    ai_seo_themes: pd.DataFrame
    ai_tools_mentions: pd.DataFrame
    seo_concepts_mentions: pd.DataFrame
    workflow_mentions: pd.DataFrame
    creator_comparison: pd.DataFrame
    topic_terms: pd.DataFrame
    research_answers: dict[str, str]


class NLPAnalyzer:
    def __init__(self) -> None:
        ensure_nltk_data()
        self._stopwords = set(stopwords.words("english"))
        self._lemmatizer = WordNetLemmatizer()
        self._custom_stop = self._stopwords | {
            "video",
            "channel",
            "youtube",
            "subscribe",
            "like",
            "going",
            "really",
            "just",
            "also",
            "one",
            "get",
            "use",
            "using",
            "make",
            "way",
        }

    def _normalize_text(self, text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s\-']", " ", text)
        return re.sub(r"\s+", " ", text).strip()

    def _tokenize(self, text: str) -> list[str]:
        tokens = word_tokenize(self._normalize_text(text))
        lemmas = []
        for token in tokens:
            if len(token) < 3 or token in self._custom_stop:
                continue
            if token.isdigit():
                continue
            lemmas.append(self._lemmatizer.lemmatize(token))
        return lemmas

    def _documents_from_df(self, cleaned_df: pd.DataFrame) -> tuple[list[str], pd.DataFrame]:
        valid = cleaned_df[cleaned_df["transcript_cleaned"].astype(str).str.len() > 0].copy()
        docs = valid["transcript_cleaned"].astype(str).tolist()
        return docs, valid

    def _keyword_frequency(self, docs: list[str]) -> pd.DataFrame:
        counter: Counter[str] = Counter()
        for doc in docs:
            counter.update(self._tokenize(doc))

        rows = [{"keyword": k, "frequency": v} for k, v in counter.most_common(NLP_SETTINGS["top_n_keywords"])]
        return pd.DataFrame(rows)

    def _ngram_analysis(self, docs: list[str]) -> pd.DataFrame:
        vectorizer = CountVectorizer(
            ngram_range=NLP_SETTINGS["ngram_range"],
            min_df=NLP_SETTINGS["min_df"],
            max_df=NLP_SETTINGS["max_df"],
            stop_words=list(self._custom_stop),
            max_features=NLP_SETTINGS["max_features"],
        )
        if not docs:
            return pd.DataFrame(columns=["ngram", "frequency"])

        matrix = vectorizer.fit_transform(docs)
        sums = np.asarray(matrix.sum(axis=0)).ravel()
        features = vectorizer.get_feature_names_out()
        ranked = sorted(zip(features, sums), key=lambda x: x[1], reverse=True)
        rows = [{"ngram": term, "frequency": int(freq)} for term, freq in ranked[: NLP_SETTINGS["top_n_keywords"]]]
        return pd.DataFrame(rows)

    def _topic_extraction(self, docs: list[str]) -> pd.DataFrame:
        if len(docs) < 3:
            return pd.DataFrame(columns=["topic_id", "term", "weight"])

        n_topics = min(NLP_SETTINGS["n_clusters"], len(docs))
        vectorizer = TfidfVectorizer(
            max_df=NLP_SETTINGS["max_df"],
            min_df=max(1, NLP_SETTINGS["min_df"] - 1),
            stop_words=list(self._custom_stop),
            ngram_range=(1, 2),
            max_features=NLP_SETTINGS["max_features"],
        )
        tfidf = vectorizer.fit_transform(docs)
        nmf = NMF(n_components=n_topics, random_state=42, max_iter=400)
        nmf.fit(tfidf)

        terms = vectorizer.get_feature_names_out()
        rows = []
        for topic_idx, topic in enumerate(nmf.components_):
            top_indices = topic.argsort()[::-1][:10]
            for rank, idx in enumerate(top_indices, start=1):
                rows.append(
                    {
                        "topic_id": topic_idx + 1,
                        "term": terms[idx],
                        "weight": float(topic[idx]),
                        "rank": rank,
                    }
                )
        return pd.DataFrame(rows)

    def _theme_clustering(self, docs: list[str], meta_df: pd.DataFrame) -> pd.DataFrame:
        if len(docs) < NLP_SETTINGS["n_clusters"]:
            meta_df = meta_df.copy()
            meta_df["cluster_id"] = 1
            meta_df["cluster_label"] = "general"
            return meta_df[["video_id", "expert_name", "cluster_id", "cluster_label"]]

        vectorizer = TfidfVectorizer(
            max_df=NLP_SETTINGS["max_df"],
            min_df=max(1, NLP_SETTINGS["min_df"] - 1),
            stop_words=list(self._custom_stop),
            ngram_range=(1, 2),
            max_features=2000,
        )
        matrix = vectorizer.fit_transform(docs)
        n_clusters = min(NLP_SETTINGS["n_clusters"], len(docs))
        model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = model.fit_predict(matrix)

        terms = vectorizer.get_feature_names_out()
        order_centroids = model.cluster_centers_.argsort()[:, ::-1]
        cluster_labels: dict[int, str] = {}
        for cluster_id in range(n_clusters):
            top_terms = [terms[i] for i in order_centroids[cluster_id, :3]]
            cluster_labels[cluster_id] = ", ".join(top_terms)

        result = meta_df.copy()
        result["cluster_id"] = labels + 1
        result["cluster_label"] = [cluster_labels[int(l)] for l in labels]
        return result[["video_id", "expert_name", "cluster_id", "cluster_label"]]

    def _count_phrases(self, docs: list[str], phrases: list[str]) -> pd.DataFrame:
        normalized_docs = [self._normalize_text(doc) for doc in docs]
        rows = []
        for phrase in phrases:
            phrase_norm = self._normalize_text(phrase)
            count = sum(normalized_doc.count(phrase_norm) for normalized_doc in normalized_docs)
            if count:
                rows.append({"phrase": phrase, "mentions": count})
        return pd.DataFrame(rows).sort_values("mentions", ascending=False).reset_index(drop=True)

    def _count_phrases_by_creator(
        self,
        cleaned_df: pd.DataFrame,
        phrases: list[str],
        category: str,
    ) -> pd.DataFrame:
        rows = []
        for expert, group in cleaned_df.groupby("expert_name"):
            docs = group["transcript_cleaned"].astype(str).tolist()
            counts = self._count_phrases(docs, phrases)
            for _, row in counts.iterrows():
                rows.append(
                    {
                        "expert_name": expert,
                        "category": category,
                        "phrase": row["phrase"],
                        "mentions": row["mentions"],
                    }
                )
        return pd.DataFrame(rows)

    def _creator_comparison(self, cleaned_df: pd.DataFrame, themes_df: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for expert, group in cleaned_df.groupby("expert_name"):
            docs = group["transcript_cleaned"].astype(str).tolist()
            all_text = " ".join(docs)
            tokens = self._tokenize(all_text)
            word_count = len(all_text.split())
            video_count = len(group)

            ai_tool_hits = self._count_phrases(docs, AI_TOOLS)["mentions"].sum() if docs else 0
            seo_hits = self._count_phrases(docs, SEO_CONCEPTS)["mentions"].sum() if docs else 0
            workflow_hits = self._count_phrases(docs, WORKFLOW_PHRASES)["mentions"].sum() if docs else 0

            expert_themes = themes_df[themes_df["expert_name"] == expert]
            top_theme = (
                expert_themes["cluster_label"].mode().iloc[0]
                if not expert_themes.empty and not expert_themes["cluster_label"].mode().empty
                else ""
            )

            rows.append(
                {
                    "expert_name": expert,
                    "videos_analyzed": video_count,
                    "total_words": word_count,
                    "unique_keywords": len(set(tokens)),
                    "ai_tool_mentions": int(ai_tool_hits),
                    "seo_concept_mentions": int(seo_hits),
                    "workflow_mentions": int(workflow_hits),
                    "dominant_theme": top_theme,
                    "avg_words_per_video": round(word_count / video_count, 1) if video_count else 0,
                }
            )

        return pd.DataFrame(rows).sort_values("videos_analyzed", ascending=False)

    def _build_research_answers(
        self,
        top_keywords: pd.DataFrame,
        ai_tools: pd.DataFrame,
        seo_concepts: pd.DataFrame,
        workflows: pd.DataFrame,
        creator_comparison: pd.DataFrame,
        topic_terms: pd.DataFrame,
    ) -> dict[str, str]:
        top_topics = ", ".join(top_keywords.head(10)["keyword"].tolist()) if not top_keywords.empty else "N/A"
        top_tools = ", ".join(ai_tools.head(10)["phrase"].tolist()) if not ai_tools.empty else "N/A"
        top_workflows = ", ".join(workflows.head(8)["phrase"].tolist()) if not workflows.empty else "N/A"

        creator_diff = ""
        if not creator_comparison.empty:
            highlights = []
            for _, row in creator_comparison.head(5).iterrows():
                highlights.append(
                    f"- **{row['expert_name']}**: dominant theme '{row['dominant_theme']}', "
                    f"{row['ai_tool_mentions']} AI tool mentions, {row['workflow_mentions']} workflow mentions"
                )
            creator_diff = "\n".join(highlights)

        topic_summary = ""
        if not topic_terms.empty:
            for topic_id in sorted(topic_terms["topic_id"].unique())[:5]:
                terms = topic_terms[topic_terms["topic_id"] == topic_id].sort_values("rank")["term"].head(5).tolist()
                topic_summary += f"- Topic {topic_id}: {', '.join(terms)}\n"

        return {
            "most_discussed_ai_seo_topics": top_topics,
            "most_mentioned_ai_tools": top_tools,
            "recommended_workflows": top_workflows,
            "creator_differences": creator_diff or "Insufficient data for creator comparison.",
            "topic_model_summary": topic_summary or "Topic modeling requires more transcript data.",
            "top_seo_concepts": ", ".join(seo_concepts.head(10)["phrase"].tolist())
            if not seo_concepts.empty
            else "N/A",
        }

    def analyze(self, cleaned_df: pd.DataFrame) -> NLPAnalysisResult:
        docs, meta_df = self._documents_from_df(cleaned_df)
        if not docs:
            logger.warning("No cleaned transcripts available for NLP analysis.")
            empty = pd.DataFrame()
            return NLPAnalysisResult(
                top_keywords=empty,
                top_ngrams=empty,
                ai_seo_themes=empty,
                ai_tools_mentions=empty,
                seo_concepts_mentions=empty,
                workflow_mentions=empty,
                creator_comparison=empty,
                topic_terms=empty,
                research_answers={},
            )

        top_keywords = self._keyword_frequency(docs)
        top_ngrams = self._ngram_analysis(docs)
        topic_terms = self._topic_extraction(docs)
        themes = self._theme_clustering(docs, meta_df)

        ai_tools = self._count_phrases(docs, AI_TOOLS)
        seo_concepts = self._count_phrases(docs, SEO_CONCEPTS)
        workflows = self._count_phrases(docs, WORKFLOW_PHRASES)

        creator_comparison = self._creator_comparison(cleaned_df, themes)

        research_answers = self._build_research_answers(
            top_keywords,
            ai_tools,
            seo_concepts,
            workflows,
            creator_comparison,
            topic_terms,
        )

        return NLPAnalysisResult(
            top_keywords=top_keywords,
            top_ngrams=top_ngrams,
            ai_seo_themes=themes,
            ai_tools_mentions=ai_tools,
            seo_concepts_mentions=seo_concepts,
            workflow_mentions=workflows,
            creator_comparison=creator_comparison,
            topic_terms=topic_terms,
            research_answers=research_answers,
        )
