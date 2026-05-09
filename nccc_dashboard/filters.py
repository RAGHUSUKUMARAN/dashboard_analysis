def apply_branch_filter(df, branch):

    if df is None or df.empty:
        return df

    if branch == "all":
        return df

    if "branch" not in df.columns:
        return df

    filtered = df[df["branch"] == branch]

    if filtered.empty:
        print(f"[WARN] No data for branch: {branch}")
        return df   # fallback

    return filtered