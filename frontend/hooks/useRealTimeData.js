import { useState, useEffect, useRef } from 'react';

export function useRealTimeData(fetchFunction, interval = 10000) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const timeoutRef = useRef(null);
  const mountedRef = useRef(true);

  const fetchData = async (silent = false) => {
    if (!mountedRef.current) return;
    
    try {
      if (!silent) setLoading(true);
      setError(null);
      
      const newData = await fetchFunction();
      
      if (mountedRef.current) {
        setData(newData);
      }
    } catch (err) {
      console.error('Data fetch error:', err);
      if (mountedRef.current) {
        setError(err.message);
      }
    } finally {
      if (mountedRef.current && !silent) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    mountedRef.current = true;
    fetchData();

    const poll = () => {
      if (mountedRef.current) {
        fetchData(true);
        timeoutRef.current = setTimeout(poll, interval);
      }
    };

    timeoutRef.current = setTimeout(poll, interval);

    return () => {
      mountedRef.current = false;
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [interval]);

  return { data, loading, error };
}