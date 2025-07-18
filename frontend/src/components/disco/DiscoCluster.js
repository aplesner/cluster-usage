import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './DiscoCluster.css';

const faqData = [
  {
    question: 'I am a student, how many GPUs am I allowed to use?',
    answer: '≤4 without reservation, otherwise contact your supervisor for a reservation.'
  },
  {
    question: 'I got an email about my cluster usage?',
    answer: 'Please reduce your GPU or IO usage accordingly. If you feel this was sent to you by mistake, please reach out to your supervisor.'
  },
  {
    question: 'Where do I see the reservations?',
    answer: (<span>Click the <Link to="/calendar">Calendar</Link> tab.</span>)
  },
  {
    question: 'How do I enter a reservation?',
    answer: (<span>Ask your supervisor who will create an entry according to the template discussed in the <Link to="/calendar">calendar</Link> reference.</span>)
  },
  {
    question: 'I have high IO usage. What should I do?',
    answer: (
      <span>
        Please discuss this with your supervisor in depth. You are likely using a dataset on <code>net_scratch</code>; ideally, you would move the dataset locally to the <code>scratch</code> partition (also your conda env or apptainer) to reduce global IO usage. Note that some services like <code>wandb</code> might create/write a lot on <code>net_scratch</code> if not specified otherwise.
      </span>
    )
  },
  {
    question: 'Someone is using GPUs that I (and my supervisor) have reserved (at least 2 days in advance).',
    answer: 'Please reach out to your supervisor. Alternatively, reach out to the student directly (but put your supervisor in CC).'
  }
];

const DiscoCluster = () => {
  const [openFaq, setOpenFaq] = useState(null);

  const toggleFaq = idx => {
    setOpenFaq(openFaq === idx ? null : idx);
  };

  return (
    <div className="disco-cluster-container">
      <h2 className="page-title">DISCO Cluster</h2>

      {/* Rules Section */}
      <div className="card">
        <div className="card-header">
          <h3>Rules</h3>
        </div>
        <div className="card-body">
          <div className="rule-box">
            <strong>I.</strong> <strong>For students:</strong> You can use a maximum of <b>&le; 4 GPUs simultaneously</b> <br/>(including interactive sessions for debugging).
          </div>
          <div className="rule-box">
            <strong>II.</strong> <strong>Keep the Cluster usable:</strong> Limit your IO usage to be under <b>100k IO operations per Hour</b> <br/>(the whole cluster is prone to go down if we go beyond 1M for a prolonged time).<br />
            Also pay attention that you do not overallocate CPUs or memory during your jobs so others can still use the resources.
          </div>
          <div className="info-box">
            If you need more, you should ask for a reservation. During a reservation, you must have high utilization; otherwise, we will notify you and your reservation may be cancelled.
          </div>
          <Link to="/calendar" className="btn btn-blue" style={{ marginBottom: '10px' }}>
            See currently active reservations
          </Link>
        </div>
      </div>

      {/* Cluster Guide Section */}
      <div className="card">
        <div className="card-header">
          <h3>Cluster Guide</h3>
        </div>
        <div className="card-body">
          <a href="https://hackmd.io/hYACdY2aR1-F3nRdU8q5dA" target="_blank" rel="noopener noreferrer">
            View the DISCO Cluster Guide
          </a>
          <ul className="guide-list">
            <li>System overview</li>
            <li>How to setup</li>
            <li>Example scripts for proper job scheduling with SLURM</li>
          </ul>
        </div>
      </div>

      {/* FAQ Section */}
      <div className="card">
        <div className="card-header">
          <h3>FAQ</h3>
        </div>
        <div className="card-body">
          <div className="faq-list">
            {faqData.map((item, idx) => (
              <div key={idx} className="faq-item">
                <button className="faq-question" onClick={() => toggleFaq(idx)}>
                  {item.question}
                  <span className="faq-toggle">{openFaq === idx ? '▲' : '▼'}</span>
                </button>
                {openFaq === idx && (
                  <div className="faq-answer">{item.answer}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DiscoCluster; 