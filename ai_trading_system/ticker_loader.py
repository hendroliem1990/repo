from data_sources.idx_data import IDXDataSource

def get_all_idx_tickers():
    """
    Get IDX tickers using the new IDXDataSource
    """
    idx_source = IDXDataSource()
    return idx_source.get_all_tickers()

# Backward compatibility
def get_idx_tickers():
    """Legacy function for backward compatibility"""
    return get_all_idx_tickers()