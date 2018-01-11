# ICS_UCI_search_engine
A search engine within the ics.uci.edu domain without the use of any indexing libraries

The HTML parser gets all text in a page, even the non-visible, such as images names. This was particularly useful for the performance of our search engine. 
Moreover, the TF-IDF measure was used to order the relevance of each document giving a specific query. For each result, the URL of the document is shown, the positions of the query in it and the TF-IDF score of the document. Many different normalization schemes of TF were tried and the best results were obtained when no normalization was used. Although this creates a bias towards documents with many terms, in our collection this works well, since we have many short documents with just a directory. In case of normalization, these non-useful documents were prioritized and documents with meaningful content were shown lower in the results. Furthermore, the pre-computed TF-IDF scores for all terms and documents in the index were used and  the results were stored for further use.
Finally, each query is preprocessed by modifying it to lowercase, removing stopwords and applying a stemmer.
