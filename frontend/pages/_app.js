import '../styles/globals.css';
import 'react-toastify/dist/ReactToastify.css';
import Layout from '../components/Layout';
import { useEffect } from 'react';
import { ToastContainer } from 'react-toastify';

export default function App({ Component, pageProps }) {
  useEffect(() => {
    // Initialize dark mode from localStorage
    const savedDarkMode = localStorage.getItem('darkMode');
    if (savedDarkMode === 'true') {
      document.documentElement.classList.add('dark');
    }
  }, []);

  return (
    <Layout>
      <Component {...pageProps} />
      <ToastContainer
        position="top-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop={false}
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="dark"
      />
    </Layout>
  );
}