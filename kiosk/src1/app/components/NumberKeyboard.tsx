type Props = {
  onInput: (value: string) => void;
};

export default function NumberKeyboard({
  onInput,
}: Props) {

  const rows = [
    ["1", "2", "3", "4", "5"],
    ["6", "7", "8", "9", "0"],
  ];

  return (

    <div className="flex flex-col gap-3 items-center mt-5">

      {rows.map((row, i) => (

        <div
          key={i}
          className="flex gap-3"
        >

          {row.map((key) => (

            <button
              key={key}
              onClick={() => onInput(key)}
              className="
                w-[85px]
                h-[75px]
                rounded-2xl
                bg-[#E5E7EB]
                text-3xl
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