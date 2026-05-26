type Props = {
  onInput: (value: string) => void;
};

export default function EnglishKeyboard({
  onInput,
}: Props) {

  const rows = [
    ["Q","W","E","R","T","Y","U","I","O","P"],
    ["A","S","D","F","G","H","J","K","L"],
    ["Z","X","C","V","B","N","M"]
  ];

  return (

    <div className="flex flex-col gap-3 items-center mt-5">

      {rows.map((row, i) => (

        <div
          key={i}
          className="flex gap-2"
        >

          {row.map((key) => (

            <button
              key={key}
              onClick={() => onInput(key)}
              className="
                w-[60px]
                h-[60px]
                rounded-2xl
                bg-[#E5E7EB]
                text-2xl
                font-bold
                shadow-sm
                active:scale-95
              "
            >
              {key}
            </button>

          ))}

        </div>

      ))}

      <button
        onClick={() => onInput("BACK")}
        className="
          w-[220px]
          h-[60px]
          rounded-2xl
          bg-[#EB5757]
          text-white
          text-2xl
          font-bold
          shadow-sm
          active:scale-95
        "
      >
        ← 삭제
      </button>

    </div>
  );
}