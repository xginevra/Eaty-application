import React, { useState } from 'react';
import { Download } from 'lucide-react';

const WeightLossDataGenerator = () => {
  const [generating, setGenerating] = useState(false);
  const [rowCount, setRowCount] = useState(5000);

  const generateData = () => {
    setGenerating(true);
    
    setTimeout(() => {
      const exercises = [
        'Gym 3x/week',
        'Cycling 4x/week',
        'Running 3x/week',
        'Swimming 2x/week',
        'HIIT 3x/week',
      ];

      const rows = [];
      
      for (let i = 0; i < rowCount; i++) {
        // Generate basic demographics
        const age = Math.floor(Math.random() * (70 - 18 + 1)) + 18;
        const sex = Math.random() > 0.5 ? 'Male' : 'Female';
        
        // Height varies by sex
        const heightMean = sex === 'Male' ? 175 : 163;
        const heightStd = 8;
        const height = Math.max(150, Math.min(200, heightMean + (Math.random() - 0.5) * 2 * heightStd * 1.5));
        
        // Starting weight - influenced by age and height
        const heightInM = height / 100;
        const baseBMI = 22 + Math.random() * 13; // BMI range 22-35
        const startWeight = baseBMI * heightInM * heightInM;
        
        // Target weight - realistic weight loss (5-20% of body weight)
        const weightLossPercent = 0.05 + Math.random() * 0.15;
        const targetWeight = startWeight * (1 - weightLossPercent);
        
        // Calculate BMIs
        const startBMI = startWeight / (heightInM * heightInM);
        const targetBMI = targetWeight / (heightInM * heightInM);
        
        // Duration - influenced by amount to lose (0.5-1kg per week is healthy)
        const weightToLose = startWeight - targetWeight;
        const weeksPerKg = 1.5 + Math.random() * 2; // 1.5-3.5 weeks per kg
        const duration = weightToLose * weeksPerKg;
        
        // Calorie intake - based on sex, age, weight
        const basalMetabolic = sex === 'Male' 
          ? 88.362 + (13.397 * startWeight) + (4.799 * height) - (5.677 * age)
          : 447.593 + (9.247 * startWeight) + (3.098 * height) - (4.330 * age);
        
        // Daily calorie intake (deficit for weight loss)
        const maintenanceCalories = basalMetabolic * 1.5;
        const deficitCalories = 300 + Math.random() * 400;
        const avgCalorieIntake = Math.round(maintenanceCalories - deficitCalories);
        
        // Calorie burn from exercise
        const exerciseIntensity = 150 + Math.random() * 500;
        const avgCalorieBurn = Math.round(exerciseIntensity);
        
        // Main exercise
        const mainExercise = exercises[Math.floor(Math.random() * exercises.length)];
        
        rows.push({
          age: Math.round(age),
          sex,
          height_cm: Math.round(height * 10) / 10,
          start_weight_kg: Math.round(startWeight * 10) / 10,
          target_weight_kg: Math.round(targetWeight * 10) / 10,
          duration_weeks: Math.round(duration * 10) / 10,
          start_bmi: Math.round(startBMI * 10) / 10,
          target_bmi: Math.round(targetBMI * 10) / 10,
          avg_calorie_intake: Math.round(avgCalorieIntake),
          avg_calorie_burn: Math.round(avgCalorieBurn),
          main_exercise: mainExercise
        });
      }
      
      // Convert to CSV
      const headers = 'age,sex,height_cm,start_weight_kg,target_weight_kg,duration_weeks,start_bmi,target_bmi,avg_calorie_intake,avg_calorie_burn,main_exercise';
      const csvContent = headers + '\n' + rows.map(row => 
        `${row.age},${row.sex},${row.height_cm},${row.start_weight_kg},${row.target_weight_kg},${row.duration_weeks},${row.start_bmi},${row.target_bmi},${row.avg_calorie_intake},${row.avg_calorie_burn},${row.main_exercise}`
      ).join('\n');
      
      // Download CSV
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `weight_loss_dataset_${rowCount}_rows.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      
      setGenerating(false);
    }, 100);
  };

  return (
    <div className="max-w-2xl mx-auto p-8">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h1 className="text-2xl font-bold mb-6 text-gray-800">
          Weight Loss Dataset Generator
        </h1>
        
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Number of Rows
          </label>
          <input
            type="number"
            value={rowCount}
            onChange={(e) => setRowCount(Math.max(1, parseInt(e.target.value) || 0))}
            className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            min="1"
            max="50000"
          />
        </div>
        
        <div className="mb-6 p-4 bg-blue-50 rounded-md">
          <h3 className="font-semibold text-blue-900 mb-2">Dataset Features:</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Age: 18-70 years</li>
            <li>• Height: Realistic by sex (M: ~175cm, F: ~163cm)</li>
            <li>• Starting BMI: 22-35 range</li>
            <li>• Weight loss: 5-20% of body weight</li>
            <li>• Duration: Based on healthy 0.3-0.7 kg/week loss</li>
            <li>• Calories: Based on BMR with deficit</li>
            <li>• Exercise: 9 different types</li>
          </ul>
        </div>
        
        <button
          onClick={generateData}
          disabled={generating}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 px-6 rounded-md transition duration-200 flex items-center justify-center gap-2"
        >
          <Download size={20} />
          {generating ? 'Generating...' : `Generate & Download ${rowCount.toLocaleString()} Rows`}
        </button>
        
        <div className="mt-4 text-xs text-gray-500">
          The CSV will download automatically when ready.
        </div>
      </div>
    </div>
  );
};

export default WeightLossDataGenerator;