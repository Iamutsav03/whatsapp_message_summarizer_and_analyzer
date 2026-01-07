from urlextract import URLExtract
extractor = URLExtract()


def most_active_users(df, top_n=10):
    contribution_df = round((df["users"].value_counts()/df.shape[0])*100 , 2).reset_index().rename(columns={'index' : 'User' , 'users' : 'Contribution(%)'})
    contribution_df.index = contribution_df.index +1
    return contribution_df.head(top_n)


# def daily_timeline(df):
#     timeline = df.groupby(df["date"].dt.date).size().reset_index(name="messages")
#     return timeline

def Link_count(df):
    return df["user_messages"].apply(lambda x: len(extractor.find_urls(x)) > 0).sum()
