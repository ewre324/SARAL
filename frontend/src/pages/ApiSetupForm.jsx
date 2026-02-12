import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { FiCpu, FiCheck, FiAlertCircle, FiInfo } from 'react-icons/fi';
import toast from 'react-hot-toast';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { apiService } from '../services/api';
import { useWorkflow } from '../contexts/WorkflowContext';

const ApiSetupForm = () => {
  const { progressToNextStep } = useWorkflow();
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState({});
  const [config, setConfig] = useState({
    ollama_url: 'http://localhost:11434',
    ollama_model: 'llama3'
  });

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      const response = await apiService.getApiKeysStatus();
      setStatus(response.data);
    } catch (error) {
      console.error('Error checking Ollama status:', error);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setConfig((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await apiService.setupApiKeys(config);
      toast.success('Ollama configured successfully!');
      await checkStatus();
      progressToNextStep();
    } catch (error) {
      console.error('Ollama setup error:', error);
      toast.error(error?.response?.data?.detail || 'Failed to configure Ollama');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">Configure Local Ollama</h2>
        <p className="text-gray-600 dark:text-gray-400">
          SARAL uses your local Ollama installation for script generation and translation.
        </p>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-neutral-800 rounded-xl p-6 border border-neutral-200 dark:border-neutral-700 space-y-6"
      >
        {loading && (
          <div className="h-1 rounded bg-gray-200 dark:bg-gray-700 overflow-hidden mb-4">
            <div className="h-full w-full animate-pulse bg-gray-700 dark:bg-gray-400" />
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Ollama URL</label>
            <input
              type="text"
              name="ollama_url"
              value={config.ollama_url}
              onChange={handleInputChange}
              className="w-full mt-2 px-3 py-2 border rounded-md bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100"
              placeholder="http://localhost:11434"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Model Name</label>
            <input
              type="text"
              name="ollama_model"
              value={config.ollama_model}
              onChange={handleInputChange}
              className="w-full mt-2 px-3 py-2 border rounded-md bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100"
              placeholder="llama3"
            />
          </div>

          <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
            {status.ollama_configured ? <FiCheck className="text-green-600" /> : <FiAlertCircle className="text-yellow-600" />}
            <span>
              {status.ollama_configured
                ? `Connected. Active model: ${status.ollama_model || config.ollama_model}`
                : 'Not validated yet. Ensure Ollama is running locally.'}
            </span>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 pt-2">
            <button
              type="submit"
              disabled={loading}
              className="flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-md bg-gray-900 hover:bg-gray-800 disabled:bg-gray-400 text-white font-medium"
            >
              {loading ? (
                <>
                  <LoadingSpinner size="sm" />
                  Validating...
                </>
              ) : (
                <>
                  <FiCpu className="w-5 h-5" />
                  Save Ollama Configuration
                </>
              )}
            </button>

            <button
              type="button"
              onClick={progressToNextStep}
              className="flex-1 px-6 py-3 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 font-medium"
            >
              Skip for Now
            </button>
          </div>
        </form>

        <div className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg text-sm text-gray-600 dark:text-gray-400 flex items-start gap-2">
          <FiInfo className="w-4 h-4 mt-0.5" />
          Ensure the model is downloaded first, for example: <code>ollama pull llama3</code>
        </div>
      </motion.div>
    </div>
  );
};

export default ApiSetupForm;
