#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
Created on Feb 25 09:27:41 2017

@author: evita
"""

import timeit
import pickle
import numpy as np
from nltk.stem.porter import PorterStemmer
from nltk.corpus import stopwords
import indexer
from google_query_fetcher import fetch_urls #our goole fetcher
                

def load_urlnames():
    #load the url of each document
    filename_to_url_dict = dict()
    urls = set()
    splitted = []
    with open('bookkeeping.tsv') as read:
        for line in read:
            splitted = line.split('\t')
            file_name = splitted[0].split("/")
            length = len(file_name)
            doc_id = file_name[length -2] + "_" + file_name[length-1]
            filename_to_url_dict[doc_id] = "http://" + splitted[1]
            urls.add(splitted[1])
    return filename_to_url_dict,urls
                    
def load_pickle(filename):
    f = open(filename,'rb')
    loaded_dict = pickle.load(f)
    f.close()
    return loaded_dict
    
def query_preprocessing(query):
    tokens = indexer.tokenize(query)
    porter = PorterStemmer()
    filtered_words = [word for word in tokens if word not in stopwords.words('english')] 
    stemmed_words = [porter.stem(word) for word in filtered_words]
    return stemmed_words
    
def single_word_query(query, main_index, filename_to_url_dict, tf_idf_dict,ideal_ranking_dict):
    actual_ranking_list = list()
    relevance_dict = dict()
    if query in main_index.keys():
        docs = main_index[query]
        print "QUERY: ",query, " -- Total results: ", len(docs)
        print "------- beginning of top 5 results-----"
        positions_url = dict()
        if len(docs)>1:
            scores = dict()
            for d in docs:
                for item in d.keys():
                    try:
                        url = filename_to_url_dict[item]
                    except:
                        "error in :",item
                        pass
                    list_terms = tf_idf_dict[item]
                    for l in list_terms:
                        if query in l.keys():
                           scores[url] = l[query]
                    #print "found in document: ", url, " (doc id: " + item + " in positions: ", d[item]
                    positions_url[url] = d[item]
            scores = sorted(scores.items(), key=lambda x:x[1], reverse=True)
            scores_top = scores[:5]
            count = 1
            for s in scores_top:
                print count,": ", s[0], "found in positions: ", positions_url[s[0]]
                print " having TF-IDF score of: ",s[1]
                url_name = s[0].rstrip()
                count += 1
            helper_counter = 0
            for s in scores:
                url_name = s[0].rstrip()
                actual_ranking_list.append(url_name)
                if url_name in ideal_ranking_dict.keys():
                    relevance_dict[url_name] = ideal_ranking_dict[url_name]
                    if helper_counter<5:
                        print 'doc',url_name,'relevance:', ideal_ranking_dict[url_name]
                else:
                    relevance_dict[url_name] = 1
                    if helper_counter <5:
                        print 'doc', url_name,'relevance:',1
                helper_counter += 1
        else:
            for d in docs[0].keys():
                print "found in document: ",filename_to_url_dict[d], "in positions:", docs[0][d]
                print " having TF-IDF score of: ", s[1]
    else:   
        print "No results found for query: ", query
    print "----- end of top 5 results ------"
    return actual_ranking_list, relevance_dict


def elastic_query(query, main_index, filename_to_url_dict, tf_idf_dict,ideal_ranking_dict):  
    #a doc must contain at least one term of the query to be considered for the results:
    sum_tf_idf_per_doc = dict()
    relevance_dict = dict()
    actual_ranking_list = list()
    count = 0
    query = set(query) #remove duplicate terms in query, each term counts once
    positions_url = dict()
    for q_term in query:
        if q_term in main_index.keys():
            count += 1
            docs = main_index[q_term]
            #total docs for that query term
            if len(docs)>1:
                for d in docs:
                    for item in d.keys():
                        try:
                            url = filename_to_url_dict[item]
                        except:
                            pass
                        if url in sum_tf_idf_per_doc.keys():
                            current_score = sum_tf_idf_per_doc[url]
                            current_positions = list()
                            current_positions = positions_url[url]
                        else:
                            current_score = 0
                            current_positions = list()
                        list_terms = tf_idf_dict[item]
                        for l in list_terms:
                            if q_term in l.keys():
                                sum_tf_idf_per_doc[url] = current_score + l[q_term]
                                if len(current_positions) > 0:
                                    positions_url[url] = current_positions + d[item]
                                else:
                                    positions_url[url] = d[item]
            else:
                count=1
                print "single doc matching the term"
    if count>1:
        sum_tf_idf_per_doc = sorted(sum_tf_idf_per_doc.items(), key=lambda x:x[1], reverse=True)
        sum_tf_idf_per_doc_top = sum_tf_idf_per_doc[:5]#print top 5
        count = 1
        for s in sum_tf_idf_per_doc_top:
            print count, " : ",s[0], "found in positions: ",positions_url[s[0]]
            print "having TF-IDF score of: ", s[1]
            url_name = s[0].rstrip()
            count += 1
        helper_counter=0
        for s in sum_tf_idf_per_doc:
            url_name = s[0].rstrip()
            actual_ranking_list.append(url_name)
            if url_name in ideal_ranking_dict.keys():
                relevance_dict[url_name] = ideal_ranking_dict[url_name]
                if helper_counter<5:
                    print 'doc',url_name,'relevance:',ideal_ranking_dict[url_name]
            else:
                relevance_dict[url_name] = 1
                if helper_counter < 5:
                    print 'doc',url_name,'relevance:',1
            helper_counter += 1
    elif count == 1:
        for d in positions_url.keys():
            print d
            print "found in document: ", filename_to_url_dict[d], "in positions:",positions_url[d]  
            print "having TF-IDF score of: ", sum_tf_idf_per_doc[d][1]          
    if count==0:   
        print "0 results found for query: ", query
    print "----- end of results ------"   
    return actual_ranking_list, relevance_dict
            

def multiple_words_query(query, main_index, filename_to_url_dict, tf_idf_dict, ideal_ranking_dict):
    #a doc must contain ALL query terms to be considered for the results:    
    sum_tf_idf_per_doc = dict()
    actual_ranking_list = list()
    count = 0
    query = set(query) #remove duplicate terms in query, each term counts once
    positions_url = dict()
    q_term_docs = dict()
    for q_term in query:
        if q_term in main_index.keys():
            count += 1
            docs = main_index[q_term]
            #total docs for that query term
            docs_set = set()
            if len(docs) > 1:
                for d in docs:
                    for item in d.keys():
                        docs_set.add(item)
                        q_term_docs[q_term] = docs_set
                        current_positions = list()
                        try:
                            url = filename_to_url_dict[item]
                        except: # error finding item
                            pass
                        if url in positions_url.keys():
                            current_positions = positions_url[url]
                            positions_url[url] = current_positions+d[item]
                        else:
                            positions_url[url]=d[item]
            else:
                print "single doc found"
                print docs
                docs_set.add(docs)
                q_term_docs[q_term] = docs_set
                if docs in positions_url.keys():
                    positions_url[item] += d[docs]
                else:
                    positions_url[item] = d[docs]
        else:
            return "No results found"
    final_docs = set()
    for q in q_term_docs.keys():
        if len(final_docs)>1:
            inters = q_term_docs[q].intersection(final_docs)
            final_docs = inters
        else:
            final_docs = q_term_docs[q]

    for d in final_docs:
        try:
           url = filename_to_url_dict[d]
        except:
            print "Error in finding ", d
            pass
        current_score = 0
        sum_tf_idf_per_doc[d] = 0
        list_terms = tf_idf_dict[d]
        for l in list_terms:
            if q in l.keys():
                current_score = l[q]
                if url in sum_tf_idf_per_doc.keys():
                    prev_score = sum_tf_idf_per_doc[url]
                    sum_tf_idf_per_doc[url] = prev_score+current_score
                else:
                    sum_tf_idf_per_doc[url] = current_score
    relevance_dict = dict()
    if len(final_docs)>1:
        sum_tf_idf_per_doc = sorted(sum_tf_idf_per_doc.items(), key=lambda x:x[1], reverse=True)
        sum_tf_idf_per_doc_top = sum_tf_idf_per_doc[:5] #print top 5
        count = 1
        for s in sum_tf_idf_per_doc_top:
            print count, " : ",s[0], "found in positions: ",positions_url[s[0]]
            print "having TF-IDF score of: ", s[1]
            count += 1
        helper_counter=0
        for s in sum_tf_idf_per_doc:
            url_name = s[0].rstrip()
            actual_ranking_list.append(url_name)
            if url_name in ideal_ranking_dict.keys():
                relevance_dict[url_name] = ideal_ranking_dict[url_name]
                if helper_counter < 5:
                    print 'doc',url_name,'relevance:', ideal_ranking_dict[url_name]
            else:
                relevance_dict[url_name]=1
                if helper_counter < 5:
                    print 'doc', url_name,'relevance:',1
            helper_counter += 1
    elif len(final_docs) == 1:
        for d in positions_url.keys():
            print d
            print "found in document: ", filename_to_url_dict[d], "in positions:", positions_url[d]  
            print "having TF-IDF score of: ", sum_tf_idf_per_doc[d][1]          
    if len(final_docs)==0:   
        print "0 results found for query: ", query
    print "----- end of results ------"   
    return actual_ranking_list, relevance_dict
          
def compute_DCG(ranking,relevance_dict):
     disc_gain_list = list()
     i = 0
     rank = 1
     for r in ranking:
         #print "doc:",r,"rank:",rank, "relevance:",relevance_dict[r]
         if i == 0:
            discount = relevance_dict[r] 
         else: 
             discount = float(relevance_dict[r] / np.log2(rank))   
         disc_gain_list.append(discount)
         i += 1
         rank += 1
     dcg = list()
     j = 0
     for d in disc_gain_list: 
       if j==0:
           cur_sum = d
           dcg.append(cur_sum)
       else:
           cur_sum += d
           dcg.append(cur_sum)
       j += 1
     return dcg
     
def main():
    filename_to_url_dict, urls = load_urlnames() 
    '''
    # Steps for building the main index from scratch:

    #1) create dictionary for each file with word positions
    indexer.create_postings_per_file(parse_docs, urls, filename_to_url_dict) 
    
    #2) create inverted index per block
    indexer.create_block_index('postings_per_file')

    #3) merge the block indexes into a single inverted index
    main_ind = indexer.merge_blocks_to_main_index()
    '''

    # 4) load the final index from file
    main_ind = dict()
    print "loading inverted index....."
    main_ind = load_pickle("final_merged_main_index.pkl")

    #basic statistics:
    print "Some statistics: "
    indexed_files = indexer.list_files('postings_per_file')
    N = len(indexed_files)
    print "total indexed files:", N
    print "vocabulary size: ", len(main_ind.keys())
    print 
    print

    #5) pre-compute TF-IDF as an index and save it to a file
    #tf_idf_dict = indexer.TF_IDF(main_ind, N)
    
    #6) load TF-IDF from file to a dictionary
    print "loading pre computed TF-IDF ....."
    tfidf_ind = load_pickle("final_tfidf_index.pkl")
    print
    print "READY!"
    print
    print
    query = ""
    while True:
        query = raw_input("Search for: ")
        if query == "exit":
            break
        print "query as entered by user: ", query
        print
        print "Google's results:"
        ideal_ranking = []
        ideal_ranking = fetch_urls(query)
        ideal_relevance_dict = dict()
        i = 5
        for d in ideal_ranking[:5]:
            ideal_relevance_dict[d] = i
            i -= 1  
        print "ground truth relevance:", ideal_relevance_dict
        ideal_dcg = compute_DCG(ideal_ranking[:5], ideal_relevance_dict)
        if len(ideal_dcg) < 5:
            ideal_dcg.append(ideal_dcg[len(ideal_dcg)-1])
        start2 = timeit.default_timer()
        preprocessed_query = query_preprocessing(query)
        print "preprocessed query: ", preprocessed_query
        print
        print "ICS Search Engine - WELCOME!"
        print
        print
        print "ICS-Search Engine Results:"
        print
        if len(preprocessed_query) == 1:
            #the case of a single-term query
            actual_ranking_list,relevance_dict = single_word_query(preprocessed_query[0], main_ind, filename_to_url_dict, tfidf_ind,ideal_relevance_dict)
            actual_dcg = compute_DCG(actual_ranking_list,relevance_dict)
            ndcg = list()
            i = 0
            while i<5:
                cur_ndcg = actual_dcg[i]/ideal_dcg[i]
                ndcg.append(cur_ndcg)
                i += 1
            if len(ndcg) > 1:    
                print "NDCG@5:",ndcg.pop() 
            else:
                print "NDCG@5 could not be calculated"
        else:
            #the case of a multiple-terms query
            actual_ranking_list,relevance_dict = elastic_query(preprocessed_query, main_ind, filename_to_url_dict, tfidf_ind,ideal_relevance_dict)
            actual_dcg = compute_DCG(actual_ranking_list,relevance_dict)
            ndcg = list()
            i = 0
            while i < 5:
                cur_ndcg = actual_dcg[i]/ideal_dcg[i]
                ndcg.append(cur_ndcg)
                i += 1
            if len(ndcg) > 1:    
                print "NDCG@5:",ndcg.pop()
            else:
                print "NDCG@5 could not be calculated"
        elapsed2 = timeit.default_timer() - start2
        print "total query response time: ",elapsed2, "seconds"
       
if __name__ == "__main__":
    main()


