import React, { useState, useEffect, useRef } from 'react';
import './index.css';

function App() {
  const [selectedImage, setSelectedImage] = useState(null);
  const [resultImage, setResultImage] = useState(null);

  const openWebcamPage = () => {
    window.open('http://localhost:8000/video_cam', '_blank');
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    setSelectedImage(file);
    const reader = new FileReader();
    reader.onloadend = () => {};
    reader.readAsDataURL(file);
  };

  const handleDetect = async () => {
    const formData = new FormData();
    formData.append('image_file', selectedImage);

    // Подключение к бэку
    const apiUrl = 'http://localhost:8000/detect';

    try {
      const response = await fetch(apiUrl, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const resultImageBlob = await response.blob();
        setResultImage(URL.createObjectURL(resultImageBlob));
      } else {
        console.error('Ошибка');
      }
    } catch (error) {
      console.error('Ошибка подключения к серверу', error);
    }
  };

  return (
    <div className="container mx-auto bg-white my-8 Bord">
      <h1 className="text-3xl font-bold mb-4">Поиск дефектов на фигурке Иноске</h1>
        <div className="mr-4">
          <input type="file" accept="image/*" onChange={handleFileChange} className="mb-4" />
          <button onClick={handleDetect} className="text-white px-4 py-2 mr-10 rounded">
            Загрузка
          </button>
          <button onClick={openWebcamPage}>
        Вебкамера
      </button>
        </div>
        
        <div className="inline-grid grid-cols-2 mb-4">
                  {/* Выбранное изображение */}
        {selectedImage && (
          <div className="flex flex-col">
            <h2 className="text-xl font-bold mb-2">Выбранное изображение</h2>
            <img src={URL.createObjectURL(selectedImage)} alt="Selected" style={{ width: '500px' }} />
          </div>
        )}

        {/* Результат */}
        {resultImage && (
          <div className="flex flex-col ml-4">
            <h2 className="text-xl font-bold mb-2">Результат</h2>
            <img src={resultImage} alt="Result" style={{ width: '500px' }} />
          </div>
        )}

        </div>

      </div>
  );
}

export default App;